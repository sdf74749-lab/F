# تحسينات شاملة لرفع جودة اللعبة (Parchis Mobile 2-4 Players)

هذا المستند يضيف طبقة **تحسين تجربة اللعب** فوق البنية الحالية (P2P + Host Migration).

## 1) تحسين الإحساس باللعب (Game Feel)

- **Turn Timer ذكي**: 20 ثانية افتراضيًا، ينخفض تدريجيًا في منتصف/نهاية المباراة لتسريع الإيقاع.
- **Auto-Move آمن** عند انتهاء الوقت: اختيار أفضل حركة قانونية تلقائيًا لمنع تعطّل الجلسة.
- **Animation Budget**: حركات القطع لا تتجاوز 350-500ms لكل خانة مع إمكانية Skip للأنيميشن عند الشبكة الضعيفة.
- **Haptic + SFX**: هزة خفيفة عند أكل قطعة/دخول البيت النهائي.

## 2) عدالة اللعب ومنع الغش

- **Deterministic Dice**: توليد رمية النرد من seed مشترك + turn index + nonce لمنع التلاعب الفردي.
- **Commit-Reveal** بين اللاعبين (الـHost + backup witness):
  1) كل طرف يرسل hash للبذرة.
  2) بعد تثبيت الدور يتم reveal.
  3) أي mismatch => علم إنذار + إنهاء الجلسة تنافسيًا.
- **State Hash كل N أحداث** (مثلاً كل 5 أحداث) للتأكد أن كل عميل يملك نفس الحالة.

## 3) استقرار الشبكة

- **Jitter Buffer صغير** (80-120ms) لتقليل تقطّع الحركة.
- **Graceful Degradation**:
  - RTT > 250ms: تقليل تردد تحديثات visual-only.
  - Packet loss > 8%: تفعيل snapshot cadence أسرع.
- **Quick Reconnect** خلال 20-30 ثانية مع delta sync بدل full state.

## 4) Host Migration أفضل

- Host أساسي + **Shadow Host** يملك snapshot/event index دائمًا.
- عند خروج الـHost:
  - shadow host يتولى خلال <= 2 ثانية.
  - إرسال `HOST_TAKEOVER` مع proof hash.
  - استكمال الدور بدون إعادة رمية.

## 5) تحسين UX

- **Ping indicator** ملون (أخضر/برتقالي/أحمر).
- **Ready Check** قبل بدء الجولة.
- **Smart AFK Handling**:
  - تحذير بعد 10 ثواني عدم تفاعل.
  - Auto-play بعد 2 أدوار AFK متتالية.

## 6) تحسين التوازن (Balance)

- جدول احتمالات/قواعد خاصة في النمط Ranked يقلل العشوائية العالية المتتالية.
- حماية اللاعب المتأخر عبر قواعد catch-up خفيفة (اختيارية حسب نمط اللعب).

## 7) تحليلات الأداء (بدون انتهاك الخصوصية)

- Metrics لكل مباراة:
  - زمن الدور المتوسط.
  - عدد انقطاعات reconnect.
  - زمن host migration.
  - نسبة إنهاء المباريات.
- استعمال IDs مجهولة + عدم تخزين أي بيانات شخصية.

## 8) خطة تنفيذ سريعة (Sprint-ready)

1. Sprint 1: Turn timer + auto-move + ping indicator.
2. Sprint 2: commit-reveal + state hash + reconnect window.
3. Sprint 3: shadow host + migration under 2s.
4. Sprint 4: ranked tuning + telemetry dashboard.
