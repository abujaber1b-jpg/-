import os
import json
import random
import string
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response
from scene_generator import generate_crime_scene_svg

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "crimson-detective-secret-key-2026")

# Load the 30 criminal cases
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE_DIR, "cases.json"), "r", encoding="utf-8") as f:
    ALL_CASES = json.load(f)

CASES_BY_ID = {c["id"]: c for c in ALL_CASES}

# In-memory game rooms store (works seamlessly on single-worker Render deployment)
GAMES = {}


def generate_code(length=6):
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(random.choice(chars) for _ in range(length))


def normalize_arabic(text):
    if not text:
        return ""
    text = text.strip().lower()
    for ch in ["أ", "إ", "آ"]:
        text = text.replace(ch, "ا")
    text = text.replace("ة", "ه").replace("ى", "ي")
    return text


def evaluate_group_answers(case_obj, ans_culprit, ans_motive, ans_contradictions):
    """
    تقييم آلي ذكي يقارن إجابات المجموعة مع الحل النموذجي ويقترح درجات مبدئية للمقدم:
    - الجاني: من 10
    - السبب وكيف تمت الجريمة: من 30
    - اكتشاف التناقضات: من 15
    """
    norm_c = normalize_arabic(ans_culprit)
    norm_m = normalize_arabic(ans_motive)
    norm_x = normalize_arabic(ans_contradictions)

    # 1. Culprit score (out of 10)
    c_keywords = [normalize_arabic(k) for k in case_obj.get("keywords_culprit", [])]
    c_hits = sum(1 for k in c_keywords if k and k in norm_c)
    if c_hits >= 1:
        auto_culprit = 10
        c_note = "مطابقة تامة لاسم الجاني في الحل النموذجي."
    elif len(norm_c) > 2:
        auto_culprit = 3
        c_note = "تم ذكر مشتبه به غير مطابق للاسم الحرفي، يُرجى مراجعة المقدم."
    else:
        auto_culprit = 0
        c_note = "لم يتم تحديد الجاني."

    # 2. Motive score (out of 30)
    m_keywords = [normalize_arabic(k) for k in case_obj.get("keywords_motive", [])]
    m_hits = sum(1 for k in m_keywords if k and k in norm_m)
    if len(m_keywords) > 0:
        ratio_m = min(1.0, m_hits / max(1, min(3, len(m_keywords))))
    else:
        ratio_m = 0
    auto_motive = round(ratio_m * 30)
    if len(norm_m) >= 25 and auto_motive < 12:
        auto_motive = 12  # حد أدنى للتحليل المكتوب بجهد
    m_note = f"طابق {m_hits} من العناصر الجوهرية للدافع وطريقة التنفيذ."

    # 3. Contradictions score (out of 15)
    x_keywords = [normalize_arabic(k) for k in case_obj.get("keywords_contradictions", [])]
    x_hits = sum(1 for k in x_keywords if k and k in norm_x)
    if len(x_keywords) > 0:
        ratio_x = min(1.0, x_hits / max(1, min(2, len(x_keywords))))
    else:
        ratio_x = 0
    auto_contradictions = round(ratio_x * 15)
    if len(norm_x) >= 20 and auto_contradictions < 6:
        auto_contradictions = 6
    x_note = f"اكتشف {x_hits} من الأدلة المتناقضة في مسرح الجريمة."

    return {
        "culprit": auto_culprit,
        "motive": auto_motive,
        "contradictions": auto_contradictions,
        "total_auto": auto_culprit + auto_motive + auto_contradictions,
        "notes": f"{c_note} | {m_note} | {x_note}"
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/scene/<int:case_id>.svg")
def case_scene_svg(case_id):
    case_obj = CASES_BY_ID.get(case_id)
    if not case_obj:
        return Response("Not found", status=404)
    svg = generate_crime_scene_svg(case_obj["id"], case_obj["title"], case_obj.get("scene_type", "vault"))
    return Response(svg, mimetype="image/svg+xml")


@app.route("/api/create_game", methods=["POST"])
def create_game():
    data = request.get_json() or {}
    host_name = (data.get("host_name") or "المقدم").strip()
    num_groups = int(data.get("num_groups") or 3)
    num_groups = max(2, min(8, num_groups))
    time_minutes = int(data.get("time_minutes") or 10)
    time_minutes = max(1, min(60, time_minutes))

    game_code = generate_code(6)
    while game_code in GAMES:
        game_code = generate_code(6)

    host_token = generate_code(12)

    # Shuffle all 30 cases randomly every time a new game starts!
    shuffled_ids = [c["id"] for c in ALL_CASES]
    random.shuffle(shuffled_ids)

    groups = []
    for i in range(num_groups):
        invite_code = generate_code(5)
        groups.append({
            "index": i,
            "invite_code": invite_code,
            "name": f"المجموعة {i + 1}",
            "joined": False,
            "players": [],
            "case_id": None,
            "opponent_group_index": None,
            "submitted": False,
            "submitted_at": None,
            "answers": {
                "culprit": "",
                "motive": "",
                "contradictions": "",
                "special_note": "",
                "opponent_rebuttal": ""
            },
            "auto_eval": None,
            "scores": {
                "culprit": 0,         # من 10
                "motive": 0,          # من 30
                "contradictions": 0,  # من 15
                "special_note": 0,    # من 5
                "presentation": 0,    # من 20 (إلقاء)
                "debate": 0           # من 20 (محاججة)
            },
            "score_reasons": {
                "culprit": "",
                "motive": "",
                "contradictions": "",
                "special_note": "",
                "presentation": "",
                "debate": ""
            },
            "graded_phase1": False,
            "graded_phase2": False
        })

    GAMES[game_code] = {
        "game_code": game_code,
        "host_name": host_name,
        "host_token": host_token,
        "num_groups": num_groups,
        "time_minutes": time_minutes,
        "phase": "lobby",  # lobby -> investigating -> debate -> results
        "timer_end": None,
        "shuffled_case_ids": shuffled_ids,
        "groups": groups,
        "winner_group_index": None,
        "created_at": datetime.now().isoformat()
    }

    return jsonify({
        "ok": True,
        "game_code": game_code,
        "host_token": host_token
    })


@app.route("/api/join_group", methods=["POST"])
def join_group():
    data = request.get_json() or {}
    game_code = (data.get("game_code") or "").strip().upper()
    invite_code = (data.get("invite_code") or "").strip().upper()
    player_name = (data.get("player_name") or "").strip()
    group_name = (data.get("group_name") or "").strip()

    game = GAMES.get(game_code)
    if not game:
        return jsonify({"ok": False, "error": "رمز الغرفة غير صحيح! تأكد من الرمز المرسل من المقدم."}), 404

    if not player_name:
        return jsonify({"ok": False, "error": "يرجى إدخال اسم اللاعب."}), 400

    target_group = None
    for g in game["groups"]:
        if g["invite_code"] == invite_code:
            target_group = g
            break

    if not target_group:
        return jsonify({"ok": False, "error": "رمز دعوة المجموعة غير صحيح!"}), 404

    if group_name:
        target_group["name"] = group_name

    target_group["joined"] = True
    if player_name not in target_group["players"]:
        target_group["players"].append(player_name)

    return jsonify({
        "ok": True,
        "game_code": game_code,
        "group_index": target_group["index"],
        "group_name": target_group["name"],
        "player_name": player_name
    })


@app.route("/api/host/state", methods=["GET"])
def host_state():
    game_code = (request.args.get("game_code") or "").strip().upper()
    host_token = (request.args.get("host_token") or "").strip()

    game = GAMES.get(game_code)
    if not game or game["host_token"] != host_token:
        return jsonify({"ok": False, "error": "غير مصرح لك بالوصول."}), 403

    # Build cases list in the game's randomized order
    randomized_cases = [CASES_BY_ID[cid] for cid in game["shuffled_case_ids"]]

    # Enrich groups with full case model answers (ONLY visible to Host!)
    enriched_groups = []
    for g in game["groups"]:
        g_copy = dict(g)
        c_obj = CASES_BY_ID.get(g["case_id"])
        g_copy["assigned_case"] = c_obj  # Includes culprit, motive_and_how, contradictions_hint!
        opp_idx = g["opponent_group_index"]
        if opp_idx is not None and 0 <= opp_idx < len(game["groups"]):
            opp_g = game["groups"][opp_idx]
            g_copy["opponent_group_name"] = opp_g["name"]
            g_copy["opponent_case"] = CASES_BY_ID.get(opp_g["case_id"])
        else:
            g_copy["opponent_group_name"] = None
            g_copy["opponent_case"] = None

        s = g["scores"]
        g_copy["total_score"] = (
            s["culprit"] + s["motive"] + s["contradictions"] +
            s["special_note"] + s["presentation"] + s["debate"]
        )
        enriched_groups.append(g_copy)

    return jsonify({
        "ok": True,
        "game": {
            "game_code": game["game_code"],
            "host_name": game["host_name"],
            "num_groups": game["num_groups"],
            "time_minutes": game["time_minutes"],
            "phase": game["phase"],
            "timer_end": game["timer_end"],
            "server_now": time.time(),
            "winner_group_index": game["winner_group_index"],
            "groups": enriched_groups
        },
        "cases": randomized_cases
    })


@app.route("/api/host/reshuffle_cases", methods=["POST"])
def reshuffle_cases():
    data = request.get_json() or {}
    game_code = (data.get("game_code") or "").strip().upper()
    host_token = (data.get("host_token") or "").strip()

    game = GAMES.get(game_code)
    if not game or game["host_token"] != host_token:
        return jsonify({"ok": False, "error": "غير مصرح."}), 403

    random.shuffle(game["shuffled_case_ids"])
    return jsonify({"ok": True})


@app.route("/api/host/setup_and_start", methods=["POST"])
def setup_and_start():
    data = request.get_json() or {}
    game_code = (data.get("game_code") or "").strip().upper()
    host_token = (data.get("host_token") or "").strip()
    assignments = data.get("assignments") or []  # list of {group_index, case_id, opponent_group_index}
    time_minutes = int(data.get("time_minutes") or game["time_minutes"] if game_code in GAMES else 10)

    game = GAMES.get(game_code)
    if not game or game["host_token"] != host_token:
        return jsonify({"ok": False, "error": "غير مصرح."}), 403

    if len(assignments) != game["num_groups"]:
        return jsonify({"ok": False, "error": "يرجى تحديد قضية وخصم لكل مجموعة."}), 400

    chosen_cases = set()
    for item in assignments:
        g_idx = int(item["group_index"])
        c_id = int(item["case_id"])
        opp_idx = int(item["opponent_group_index"])

        if c_id not in CASES_BY_ID:
            return jsonify({"ok": False, "error": "قضية غير صالحة."}), 400
        if c_id in chosen_cases:
            return jsonify({"ok": False, "error": "لا يمكن تكرار نفس القضية لمجموعتين! اختر قضية مختلفة لكل مجموعة."}), 400
        if opp_idx == g_idx or not (0 <= opp_idx < game["num_groups"]):
            return jsonify({"ok": False, "error": "يجب اختيار مجموعة خصم مختلفة لكل مجموعة."}), 400

        chosen_cases.add(c_id)
        game["groups"][g_idx]["case_id"] = c_id
        game["groups"][g_idx]["opponent_group_index"] = opp_idx

    game["time_minutes"] = max(1, min(60, time_minutes))
    game["phase"] = "investigating"
    game["timer_end"] = time.time() + (game["time_minutes"] * 60)

    return jsonify({"ok": True})


@app.route("/api/host/update_timer", methods=["POST"])
def update_timer():
    data = request.get_json() or {}
    game_code = (data.get("game_code") or "").strip().upper()
    host_token = (data.get("host_token") or "").strip()
    extra_seconds = int(data.get("extra_seconds") or 60)

    game = GAMES.get(game_code)
    if not game or game["host_token"] != host_token:
        return jsonify({"ok": False, "error": "غير مصرح."}), 403

    now = time.time()
    base = game["timer_end"] if (game["timer_end"] and game["timer_end"] > now) else now
    game["timer_end"] = base + extra_seconds
    return jsonify({"ok": True})


@app.route("/api/host/grade_phase1", methods=["POST"])
def grade_phase1():
    data = request.get_json() or {}
    game_code = (data.get("game_code") or "").strip().upper()
    host_token = (data.get("host_token") or "").strip()
    g_idx = int(data.get("group_index"))

    game = GAMES.get(game_code)
    if not game or game["host_token"] != host_token:
        return jsonify({"ok": False, "error": "غير مصرح."}), 403

    g = game["groups"][g_idx]
    c_score = max(0, min(10, int(data.get("culprit") or 0)))
    m_score = max(0, min(30, int(data.get("motive") or 0)))
    x_score = max(0, min(15, int(data.get("contradictions") or 0)))
    s_score = max(0, min(5, int(data.get("special_note") or 0)))

    g["scores"]["culprit"] = c_score
    g["scores"]["motive"] = m_score
    g["scores"]["contradictions"] = x_score
    g["scores"]["special_note"] = s_score

    g["score_reasons"]["culprit"] = (data.get("reason_culprit") or "").strip()
    g["score_reasons"]["motive"] = (data.get("reason_motive") or "").strip()
    g["score_reasons"]["contradictions"] = (data.get("reason_contradictions") or "").strip()
    g["score_reasons"]["special_note"] = (data.get("reason_special_note") or "").strip()
    g["graded_phase1"] = True

    return jsonify({"ok": True})


@app.route("/api/host/start_debate", methods=["POST"])
def start_debate():
    data = request.get_json() or {}
    game_code = (data.get("game_code") or "").strip().upper()
    host_token = (data.get("host_token") or "").strip()

    game = GAMES.get(game_code)
    if not game or game["host_token"] != host_token:
        return jsonify({"ok": False, "error": "غير مصرح."}), 403

    game["phase"] = "debate"
    return jsonify({"ok": True})


@app.route("/api/host/grade_phase2", methods=["POST"])
def grade_phase2():
    data = request.get_json() or {}
    game_code = (data.get("game_code") or "").strip().upper()
    host_token = (data.get("host_token") or "").strip()
    g_idx = int(data.get("group_index"))

    game = GAMES.get(game_code)
    if not game or game["host_token"] != host_token:
        return jsonify({"ok": False, "error": "غير مصرح."}), 403

    g = game["groups"][g_idx]
    p_score = max(0, min(20, int(data.get("presentation") or 0)))
    d_score = max(0, min(20, int(data.get("debate") or 0)))

    g["scores"]["presentation"] = p_score
    g["scores"]["debate"] = d_score
    g["score_reasons"]["presentation"] = (data.get("reason_presentation") or "").strip()
    g["score_reasons"]["debate"] = (data.get("reason_debate") or "").strip()
    g["graded_phase2"] = True

    return jsonify({"ok": True})


@app.route("/api/host/announce_winner", methods=["POST"])
def announce_winner():
    data = request.get_json() or {}
    game_code = (data.get("game_code") or "").strip().upper()
    host_token = (data.get("host_token") or "").strip()

    game = GAMES.get(game_code)
    if not game or game["host_token"] != host_token:
        return jsonify({"ok": False, "error": "غير مصرح."}), 403

    best_idx = 0
    best_score = -1
    for g in game["groups"]:
        s = g["scores"]
        total = s["culprit"] + s["motive"] + s["contradictions"] + s["special_note"] + s["presentation"] + s["debate"]
        if total > best_score:
            best_score = total
            best_idx = g["index"]

    game["winner_group_index"] = best_idx
    game["phase"] = "results"
    return jsonify({"ok": True, "winner_group_index": best_idx})


@app.route("/api/player/state", methods=["GET"])
def player_state():
    game_code = (request.args.get("game_code") or "").strip().upper()
    group_index = int(request.args.get("group_index") or 0)

    game = GAMES.get(game_code)
    if not game or not (0 <= group_index < len(game["groups"])):
        return jsonify({"ok": False, "error": "اللعبة غير موجودة."}), 404

    g = game["groups"][group_index]
    phase = game["phase"]

    # IMPORTANT: Never expose model answers (culprit, motive_and_how, contradictions_hint) to players!
    # Also NEVER expose ANY scores until phase == 'results'!
    my_case_safe = None
    if g["case_id"] and g["case_id"] in CASES_BY_ID:
        c = CASES_BY_ID[g["case_id"]]
        my_case_safe = {
            "id": c["id"],
            "title": c["title"],
            "category": c["category"],
            "story": c["story"]
        }

    opp_info_safe = None
    opp_idx = g["opponent_group_index"]
    if opp_idx is not None and 0 <= opp_idx < len(game["groups"]):
        opp_g = game["groups"][opp_idx]
        if opp_g["case_id"] and opp_g["case_id"] in CASES_BY_ID:
            oc = CASES_BY_ID[opp_g["case_id"]]
            opp_info_safe = {
                "group_name": opp_g["name"],
                "case_id": oc["id"],
                "case_title": oc["title"],
                "case_summary": oc["summary_for_host"],  # قضية الخصم مختصرة لتجهيز المحاججة
                "case_story": oc["story"]
            }

    payload = {
        "ok": True,
        "phase": phase,
        "game_code": game["game_code"],
        "host_name": game["host_name"],
        "timer_end": game["timer_end"],
        "server_now": time.time(),
        "group": {
            "index": g["index"],
            "name": g["name"],
            "players": g["players"],
            "submitted": g["submitted"],
            "answers": g["answers"]
        },
        "my_case": my_case_safe,
        "opponent": opp_info_safe,
        "all_groups_status": [
            {"name": item["name"], "joined": item["joined"], "submitted": item["submitted"], "players": item["players"]}
            for item in game["groups"]
        ]
    }

    # Only reveal final personal score + reasons when host finishes all grading and announces results!
    if phase == "results":
        s = g["scores"]
        total = s["culprit"] + s["motive"] + s["contradictions"] + s["special_note"] + s["presentation"] + s["debate"]
        winner_g = game["groups"][game["winner_group_index"]] if game["winner_group_index"] is not None else None
        payload["final_result"] = {
            "scores": s,
            "reasons": g["score_reasons"],
            "total": total,
            "is_winner": (game["winner_group_index"] == g["index"]),
            "winner_name": winner_g["name"] if winner_g else ""
        }

    return jsonify(payload)


@app.route("/api/player/submit", methods=["POST"])
def player_submit():
    data = request.get_json() or {}
    game_code = (data.get("game_code") or "").strip().upper()
    group_index = int(data.get("group_index") or 0)

    game = GAMES.get(game_code)
    if not game or not (0 <= group_index < len(game["groups"])):
        return jsonify({"ok": False, "error": "اللعبة غير موجودة."}), 404

    if game["phase"] != "investigating":
        return jsonify({"ok": False, "error": "انتهى وقت التحقيق والتسليم."}), 400

    g = game["groups"][group_index]
    if g["submitted"]:
        return jsonify({"ok": False, "error": "تم إرسال إجابات مجموعتكم مسبقاً للمقدم."}), 400

    ans_culprit = (data.get("culprit") or "").strip()
    ans_motive = (data.get("motive") or "").strip()
    ans_contradictions = (data.get("contradictions") or "").strip()
    ans_special = (data.get("special_note") or "").strip()
    ans_rebuttal = (data.get("opponent_rebuttal") or "").strip()

    if not ans_culprit or not ans_motive:
        return jsonify({"ok": False, "error": "يرجى تعبئة خانة (من هو الجاني) وخانة (السبب وكيف تمت الجريمة) على الأقل."}), 400

    g["answers"] = {
        "culprit": ans_culprit,
        "motive": ans_motive,
        "contradictions": ans_contradictions,
        "special_note": ans_special,
        "opponent_rebuttal": ans_rebuttal
    }
    g["submitted"] = True
    g["submitted_at"] = datetime.now().strftime("%H:%M:%S")

    # Run automatic comparison against model answer for Host's reference
    case_obj = CASES_BY_ID.get(g["case_id"])
    if case_obj:
        g["auto_eval"] = evaluate_group_answers(case_obj, ans_culprit, ans_motive, ans_contradictions)

    return jsonify({"ok": True})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
