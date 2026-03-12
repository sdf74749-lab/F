# تطبيق تجريبي P2P (بدون سيرفر مركزي)

هذا تطبيق Prototype قابل للتشغيل يثبت عمليًا:

- دعم 2 إلى 4 لاعبين.
- انتخاب Host وShadow Host.
- Host Migration عند خروج المضيف.
- سياسة الدور (Turn timer + AFK autoplay).
- Dice commit-reveal deterministic لمنع التلاعب.

## التشغيل

```bash
python3 app/p2p_game_app.py --players 4 --turns 8
```

## مخرجات متوقعة

- طباعة هوية Host وShadow Host.
- طباعة نتيجة كل دور (من اللاعب، قيمة النرد، وهل حدث autoplay).
- محاكاة خروج Host أثناء الجلسة وترحيل الاستضافة تلقائيًا.
