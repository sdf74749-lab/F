# تصميم لعبة Parchis متعددة اللاعبين بدون سيرفر مركزي

هذا المستند يحوّل طلبك إلى **خطة تنفيذ عملية** باستخدام الملف المضغوط الموجود في المستودع (`Parchis-master.zip`) كنواة للعبة، مع إضافة بنية Multiplayer حديثة.

## المتطلبات التي تم تغطيتها

- بدون سيرفر مركزي دائم (P2P + Relay/STUN/TURN عند الحاجة فقط للاتصال).
- لاعب يصبح Host أثناء الجلسة.
- Host Migration تلقائي إذا خرج الـHost.
- دعم 2 إلى 4 لاعبين.
- عمل اللعبة على iOS وAndroid (مستهدف Unity/Netcode أو بديل مماثل).
- دعم بيانات لعبة كبيرة ومشفرة (حتى 12,000,000 سجل) عبر ملف مضغوط.
- تحسين جودة اللعب، العدالة، وUX (turn timer، reconnect، anti-cheat، telemetry).

## مقترح التقنية

1. **محرك اللعبة**: Unity (C#) لسهولة النشر على iOS/Android.
2. **الشبكة**:
   - Topology: Client-hosted P2P.
   - Relay اختياري لتمرير الاتصال خلف NAT (ليس Game Server مركزي).
   - مزامنة الحالة عبر Snapshot + Event Log.
3. **البيانات**:
   - ملف `game_catalog.enc.gz` مشفر (stream cipher + HMAC) مع مفتاح 256-bit.
   - تحميله محليًا على الجهاز مع فك ضغط وتحقق integrity.

## سير اللعب المختصر

1. أول لاعب ينشئ غرفة => يصبح Host.
2. يدخل 1-3 لاعبين إضافيين.
3. كل حركة تُسجل كحدث deterministic.
4. عند خروج Host:
   - يتم انتخاب Host جديد آليًا حسب جودة الشبكة/البطارية/أولوية الانضمام.
   - آخر Snapshot + Event Index تنتقل للـHost الجديد.
   - يستأنف اللعب خلال ثوانٍ بدون فقدان الدور.

## ملفات هذا التنفيذ داخل المستودع

- `prototype/HostMigrationManager.cs`: نموذج لانتخاب Host الجديد + Shadow Host.
- `prototype/TurnPolicy.cs`: سياسات الدور (مؤقت الدور + AFK + Auto Move).
- `tools/generate_encrypted_catalog.py`: مولد ملف بيانات مشفرة ومضغوطة (افتراضيًا 12 مليون سجل).
- `tools/verify_encrypted_catalog.py`: فحص سلامة ملف البيانات المشفرة.
- `docs/host_migration_protocol.md`: بروتوكول تفصيلي للهجرة.
- `docs/gameplay_improvements_ar.md`: كل تحسينات الجودة والتوازن وUX.

## تشغيل مولّد البيانات

```bash
python3 tools/generate_encrypted_catalog.py --count 10000
```

## فحص الملف المشفر

```bash
python3 tools/verify_encrypted_catalog.py --in build/game_catalog.enc.gz --key build/game_catalog.key --sample 100
```

> غيّر `--count` إلى `12000000` للإنتاج النهائي على بيئة build قوية.

## ملاحظات عملية

- 12 مليون سجل قد ينتج ملفًا كبيرًا؛ يُفضّل Chunking أو تقسيمه حسب المنطقة/النمط.
- احتفظ بمفتاح التشفير في Secure Enclave/Keystore وليس داخل النص البرمجي.
- على iOS/Android استخدم reconnect window (مثلاً 20 ثانية) أثناء host migration.
