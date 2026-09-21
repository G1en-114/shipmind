# Skill 输出契约说明

每个可执行 Skill 目录下有 `contract.json`，Harness 在把结果传给下游之前强校验：

```json
{
  "required": ["level", "evidence"],
  "types": {"level": "string", "evidence": "array"}
}
```

- 支持的类型：`string / number / boolean / array / object`
- 缺必填字段或类型不符 → 本步失败并重试，**残缺结果不得进入下游**
- 最终回复的最后一个非空行必须是纯文本 `MEDIA:<绝对路径>`（输出回传契约）

## 当前契约

| Skill | 契约文件 | 关键必填 |
|---|---|---|
| engine-room-acoustic-sentinel | contract.json | level, evidence |
| route-deviation-watch | contract.json | level, max_xte_m, n_fixes |
| radar-ppi-interpreter | contract.json | targets |
| sonar-acoustic-fingerprint | contract.json | label, confidence, mode |
| navlog-autofill | contract.json | log_text, n_events |
