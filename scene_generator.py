import html

def generate_crime_scene_svg(case_id, title, scene_type):
    # Rich dark noir & crimson crime scene SVG generator tailored to each case
    accents = {
        "vault": ("#dc2626", "خزينة البنك المصفحة • مسرح جريمة #01"),
        "poison": ("#991b1b", "قاعة العشاء الملكية • تحليل السموم #02"),
        "elevator": ("#b91c1c", "المصعد الزجاجي - الطابق 10 • مقذوفات #03"),
        "yacht": ("#ea580c", "حطام اليخت المحترق • الطب الشرعي #04"),
        "studio": ("#dc2626", "استوديو الصوت المعزول • صعق كهربائي #05"),
        "boxing": ("#b91c1c", "حلبة الملاكمة • فحص الأدلة الجنائية #06"),
        "train": ("#991b1b", "قطار منتصف الليل • المقصورة 4 #07"),
        "lab": ("#dc2626", "مختبر العزل البيولوجي • خطر كيميائي #08"),
        "museum": ("#b91c1c", "قاعة المتحف الكبرى • رسالة الدم #09"),
        "sky": ("#dc2626", "منطقة السقوط الحر • فحص المظلة #10"),
        "bath": ("#991b1b", "الجناح الخاص • مسرح جريمة منزلي #11"),
        "mine": ("#ea580c", "نفق المنجم - عمق 300م • متفجرات #12"),
        "clinic": ("#dc2626", "عيادة الأسنان • تحليل السموم #13"),
        "forest": ("#b91c1c", "غابة الصيد • مسار المقذوفات #14"),
        "sauna": ("#dc2626", "غرفة الساونا البخارية • سلاح مفقود #15"),
        "chess": ("#b91c1c", "قاعة بطولة الشطرنج • دائرة صعق #16"),
        "snow": ("#dc2626", "الكوخ الجبلي المعزول • آثار الثلج #17"),
        "circus": ("#b91c1c", "خيمة السيرك الرئيسية • عجلة الخطر #18"),
        "cinema": ("#dc2626", "بلاتوه التصوير • فحص الأسلحة #19"),
        "library": ("#ea580c", "مكتبة المخطوطات • حريق عمد #20"),
        "car": ("#b91c1c", "المنحدر الجبلي • فحص المكابح #21"),
        "aquarium": ("#dc2626", "حوض القروش العملاق • دليل بيولوجي #22"),
        "tea": ("#991b1b", "جناح الرعاية • تحليل كيميائي #23"),
        "camera": ("#dc2626", "شقة المصور • تحليل الصورة الأخيرة #24"),
        "fashion": ("#b91c1c", "كواليس عرض الأزياء • سم تلامسي #25"),
        "observatory": ("#dc2626", "قبة المرصد الفلكي • شرفة التلسكوب #26"),
        "hammam": ("#991b1b", "الحمام التركي • أداة الجريمة #27"),
        "cellar": ("#b91c1c", "قبو التخزين الأرضي • اختناق #28"),
        "theater": ("#dc2626", "خشبة المسرح المظلمة • أثر فوسفوري #29"),
        "factory": ("#ea580c", "مصنع الزجاج المنصهر • كاميرا حرارية #30"),
    }
    color, subtitle = accents.get(scene_type, ("#dc2626", f"ملف جنائي سري #{case_id:02d}"))
    safe_title = html.escape(title)
    safe_sub = html.escape(subtitle)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 320" width="100%" height="100%">
  <defs>
    <radialGradient id="bgGrad{case_id}" cx="50%" cy="45%" r="70%">
      <stop offset="0%" stop-color="#1f1216"/>
      <stop offset="65%" stop-color="#0f0a0c"/>
      <stop offset="100%" stop-color="#050304"/>
    </radialGradient>
    <radialGradient id="bloodPool{case_id}" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#7f1d1d" stop-opacity="0.9"/>
      <stop offset="60%" stop-color="#991b1b" stop-opacity="0.55"/>
      <stop offset="100%" stop-color="#450a0a" stop-opacity="0"/>
    </radialGradient>
    <pattern id="grid{case_id}" width="32" height="32" patternUnits="userSpaceOnUse">
      <path d="M 32 0 L 0 0 0 32" fill="none" stroke="#ffffff" stroke-opacity="0.04" stroke-width="1"/>
    </pattern>
  </defs>

  <rect width="800" height="320" fill="url(#bgGrad{case_id})"/>
  <rect width="800" height="320" fill="url(#grid{case_id})"/>

  <!-- Spotlight cone -->
  <polygon points="400,0 160,320 640,320" fill="#ffffff" fill-opacity="0.03"/>

  <!-- Blood splatter & forensic pool -->
  <ellipse cx="410" cy="235" rx="170" ry="38" fill="url(#bloodPool{case_id})"/>
  <circle cx="310" cy="215" r="7" fill="#991b1b" opacity="0.75"/>
  <circle cx="520" cy="245" r="10" fill="#7f1d1d" opacity="0.8"/>
  <circle cx="495" cy="210" r="4" fill="#dc2626" opacity="0.7"/>
  <circle cx="340" cy="255" r="5" fill="#991b1b" opacity="0.7"/>

  <!-- Chalk / Forensic Outline -->
  <g stroke="#e5e7eb" stroke-width="2.5" stroke-dasharray="8,6" fill="none" opacity="0.55">
    <circle cx="385" cy="185" r="16"/>
    <path d="M 372 200 L 340 225 M 398 200 L 445 215 M 385 201 L 395 245 M 395 245 L 365 275 M 395 245 L 435 270"/>
  </g>

  <!-- Evidence Markers (Yellow Forensic Tent Cards) -->
  <g transform="translate(265, 210)">
    <polygon points="0,24 12,0 24,24" fill="#facc15" stroke="#ca8a04" stroke-width="1.5"/>
    <text x="12" y="19" font-family="sans-serif" font-size="11" font-weight="bold" fill="#000" text-anchor="middle">1</text>
  </g>
  <g transform="translate(505, 195)">
    <polygon points="0,24 12,0 24,24" fill="#facc15" stroke="#ca8a04" stroke-width="1.5"/>
    <text x="12" y="19" font-family="sans-serif" font-size="11" font-weight="bold" fill="#000" text-anchor="middle">2</text>
  </g>

  <!-- Crime Scene Tape Across Corners -->
  <g transform="rotate(-7 400 45)">
    <rect x="-40" y="28" width="880" height="24" fill="#eab308" opacity="0.9"/>
    <text x="400" y="45" font-family="sans-serif" font-size="12" font-weight="900" fill="#111827" text-anchor="middle" letter-spacing="2">
      CRIME SCENE DO NOT CROSS • مسرح جريمة - ممنوع الاقتراب • EVIDENCE #{case_id:02d}
    </text>
  </g>

  <!-- Target Reticle & Fingerprint Watermark -->
  <g stroke="{color}" stroke-width="1.2" fill="none" opacity="0.35">
    <circle cx="690" cy="145" r="45"/>
    <circle cx="690" cy="145" r="30"/>
    <line x1="635" y1="145" x2="745" y2="145"/>
    <line x1="690" y1="90" x2="690" y2="200"/>
  </g>

  <!-- Case Badge & Title Overlay -->
  <rect x="30" y="82" width="130" height="26" rx="4" fill="{color}"/>
  <text x="95" y="99" font-family="sans-serif" font-size="12" font-weight="bold" fill="#ffffff" text-anchor="middle">
    ملف سري #{case_id:02d}
  </text>

  <text x="765" y="128" font-family="sans-serif" font-size="26" font-weight="900" fill="#f9fafb" text-anchor="end">
    {safe_title}
  </text>
  <text x="765" y="155" font-family="sans-serif" font-size="14" font-weight="600" fill="#fca5a5" text-anchor="end">
    {safe_sub}
  </text>

  <!-- Bottom Forensic Bar -->
  <rect x="0" y="294" width="800" height="26" fill="#000000" fill-opacity="0.75"/>
  <text x="20" y="311" font-family="monospace" font-size="11" fill="#9ca3af">
    CASE_REF: KSA-CRIM-{case_id:03d} | STATUS: ACTIVE INVESTIGATION | FORENSIC UNIT
  </text>
</svg>"""
    return svg
