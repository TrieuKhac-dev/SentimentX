# experiment_registry

```mermaid
graph LR
  n1["qwen3-4b-instruct-2507/prompt-one-turn/exp001:63c3bf0a"]
  n2["cosmetics-ds0.2.0-pl0.2.0-srccosmetics@0.1.0-e616c1e3"]
  n3["qwen3-4b-instruct-2507/prompt-cot/exp007:1d3e96c4"]
  n4["qwen3-4b-instruct-2507/prompt-cot/exp002:8d2a31b4"]
  n5["qwen3-4b-instruct-2507/prompt-cot/exp003:4553090a"]
  n6["qwen3-4b-instruct-2507/prompt-cot/exp005:d4c5f94b"]
  n7["qwen3-4b-instruct-2507/prompt-cot/exp006:43aeb425"]
  n8["phobert-base-v2/lora/exp001:363c224e"]
  n9["visobert/lora/exp001:83dff5ee"]
  n10["qwen3-4b-instruct-2507/prompt-cot/exp004:8b07affe"]
  n11["phobert-base-v2/lora/exp002:61097598"]
  n12["visobert/lora/exp002:384b271d"]
  n13["qwen3-4b-instruct-2507/prompt-cot/exp008:d2ef77a9"]
  n14["qwen3-4b-instruct-2507/prompt-cot/exp009:7cf3331e"]
  n15["qwen3-4b-instruct-2507/prompt-cot/exp011:3c5cf0a0"]
  n16["qwen3-4b-instruct-2507/prompt-cot/exp012:33c2d270"]
  n17["qwen3-4b-instruct-2507/prompt-cot/exp013:779e8738"]
  n18["qwen3-4b-instruct-2507/prompt-cot/exp010:7011d28f"]
  n1 -->|NEW| n2
  n3 -->|NEW| n2
  n4 -->|NEW| n2
  n5 -->|NEW| n2
  n6 -->|NEW| n2
  n7 -->|NEW| n2
  n8 -->|NEW| n2
  n9 -->|NEW| n2
  n10 -->|RESUME| n2
  n11 -->|NEW| n2
  n12 -->|NEW| n2
  n13 -->|NEW| n2
  n14 -->|NEW| n2
  n15 -->|NEW| n2
  n16 -->|NEW| n2
  n17 -->|NEW| n2
  n18 -->|RESUME| n2
```
