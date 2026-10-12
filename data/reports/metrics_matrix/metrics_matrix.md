# metrics_matrix

```mermaid
graph LR
  n1["<công bố COT+0-shot>"]
  n2["qwen3-4b-instruct-2507 exp002"]
  n3["qwen3-4b-instruct-2507 exp005"]
  n4["qwen3-4b-instruct-2507 exp008"]
  n5["qwen3-0.6b exp001"]
  n6["qwen2.5-0.5b-instruct exp001"]
  n7["qwen3-8b exp001"]
  n8["mistral-7b-instruct-v0.3 exp001"]
  n9["<công bố COT+1-shot>"]
  n10["qwen3-4b-instruct-2507 exp003"]
  n11["qwen3-4b-instruct-2507 exp006"]
  n12["qwen3-4b-instruct-2507 exp009"]
  n13["qwen3-4b-instruct-2507 exp011"]
  n14["qwen3-4b-instruct-2507 exp012"]
  n15["qwen3-4b-instruct-2507 exp013"]
  n16["qwen3-4b-instruct-2507 exp017"]
  n17["qwen3-0.6b exp004"]
  n18["qwen3-0.6b exp002"]
  n19["qwen3-4b-instruct-2507 exp014"]
  n20["qwen3-4b-instruct-2507 exp015"]
  n21["qwen2.5-0.5b-instruct exp002"]
  n22["qwen3-0.6b exp005"]
  n23["qwen3-8b exp002"]
  n24["mistral-7b-instruct-v0.3 exp002"]
  n25["<công bố COT+5-shot>"]
  n26["qwen3-4b-instruct-2507 exp007"]
  n27["qwen3-4b-instruct-2507 exp004"]
  n28["qwen3-4b-instruct-2507 exp010"]
  n29["qwen3-0.6b exp003"]
  n30["qwen2.5-0.5b-instruct exp003"]
  n31["qwen3-8b exp003"]
  n32["mistral-7b-instruct-v0.3 exp003"]
  n33["qwen3-4b-instruct-2507 exp001"]
  n34["phobert-base-v2 exp001"]
  n35["visobert exp001"]
  n36["phobert-base-v2 exp002"]
  n37["visobert exp002"]
  n38["qwen3-4b-instruct-2507 exp016"]
  n39["phobert-base-v2 exp003"]
  n40["visobert exp003"]
  n41["visobert exp005"]
  n42["phobert-base-v2 exp005"]
  n43["visobert exp004"]
  n44["phobert-base-v2 exp004"]
  n45["vibert-base-cased exp001"]
  n46["vibert-base-cased exp002"]
  n47["cafebert exp001"]
  n48["xlm-roberta-base exp002"]
  n49["xlm-roberta-base exp001"]
  n50["phobert-large exp002"]
  n51["phobert-large exp001"]
  n52["cafebert exp002"]
  n53["qwen3-0.6b exp001 #2"]
  n54["cafebert exp003"]
  n55["vibert-base-cased exp003"]
  n56["cafebert exp004"]
  n57["xlm-roberta-base exp003"]
  n58["vibert-base-cased exp004"]
  n59["phobert-large exp003"]
  n60["cafebert exp005"]
  n61["qwen3-4b-instruct-2507 exp004 #2"]
  n62["phobert-base-v2 exp006"]
  n63["qwen3-4b-instruct-2507 exp005 #2"]
  n64["qwen3-4b-instruct-2507 exp002 #2"]
  n65["qwen3-4b-instruct-2507 exp007 #2"]
  n66["qwen3-4b-instruct-2507 exp006 #2"]
  n67["qwen3-4b-instruct-2507 exp001 #2"]
  n68["qwen3-4b-instruct-2507 exp003 #2"]
  n69["cafebert exp006"]
  n70["phobert-base-v2 exp007"]
  n71["phobert-base-v2 exp001 #2"]
  n72["cafebert exp007"]
  n73["cafebert exp009"]
  n74["cafebert exp011"]
  n75["cafebert exp014"]
  n76["cafebert exp015"]
  n77["cafebert exp013"]
  n78["cafebert exp008"]
  n79["cafebert exp002 #2"]
  n80["cafebert exp016"]
  n81["cafebert exp017"]
  n82["cafebert exp018"]
  n83["phobert-base-v2 exp001 #3"]
  n84["cafebert exp001 #2"]
  n85["phobert-base-v2 exp002 #2"]
  n86["cafebert exp019"]
  n87["phobert-base-v2 exp002 #3"]
  n88["phobert-base-v2 exp008"]
  n89["phobert-base-v2 exp009"]
  n90["phobert-base-v2 exp010"]
  n91["phobert-base-v2 exp011"]
  n92["phobert-base-v2 exp012"]
  n93["visobert exp006"]
  n94["visobert exp009"]
  n95["visobert exp008"]
  n96["visobert exp007"]
  n97["phobert-base-v2 exp013"]
  n98["phobert-base-v2 exp014"]
  n99["phobert-base-v2 exp015"]
  n100["phobert-base-v2 exp016"]
  n101["phobert-base-v2 exp018"]
  n102["phobert-base-v2 exp019"]
  n103["phobert-base-v2 exp020"]
  n104["exp023"]
  n105["phobert-base-v2 exp021"]
  n106["exp022"]
  n107["cafebert exp012"]
  n108["phobert-base-v2 exp017"]
  n109["cafebert exp010"]
  n110["cafebert exp020"]
  n111["cafebert exp021"]
  n112["exp024"]
  n113["exp025"]
  n114["exp027"]
  n115["exp028"]
  n116["exp030"]
  n117["exp033"]
  n118["exp044"]
  n119["exp045"]
  n120["exp046"]
  n121["exp047"]
  n122["exp048"]
  n123["exp050"]
  n124["exp051"]
  n125["exp053"]
  n126["exp052"]
  n127["exp054"]
  n128["exp040"]
  n129["exp041"]
  n130["exp043"]
  n131["exp042"]
  n132["exp049"]
  n133["cosmetics-ds0.2.0-pl0.2.0-srccosmetics@0.1.0-e616c1e3"]
  n134["cosmetics-ds0.3.0-pl0.3.0-srccosmetics@0.1.0-daebf6ba"]
  n1 -->|so với| n2
  n1 -->|so với| n3
  n1 -->|so với| n4
  n1 -->|so với| n5
  n1 -->|so với| n6
  n1 -->|so với| n7
  n1 -->|so với| n8
  n9 -->|so với| n10
  n9 -->|so với| n11
  n9 -->|so với| n12
  n9 -->|so với| n13
  n9 -->|so với| n14
  n9 -->|so với| n15
  n9 -->|so với| n16
  n9 -->|so với| n17
  n9 -->|so với| n18
  n9 -->|so với| n19
  n9 -->|so với| n20
  n9 -->|so với| n21
  n9 -->|so với| n22
  n9 -->|so với| n23
  n9 -->|so với| n24
  n25 -->|so với| n26
  n25 -->|so với| n27
  n25 -->|so với| n28
  n25 -->|so với| n29
  n25 -->|so với| n30
  n25 -->|so với| n31
  n25 -->|so với| n32
  n1 -->|so với| n33
  n1 -->|so với| n34
  n1 -->|so với| n35
  n1 -->|so với| n36
  n1 -->|so với| n37
  n1 -->|so với| n38
  n1 -->|so với| n39
  n1 -->|so với| n40
  n1 -->|so với| n41
  n1 -->|so với| n42
  n1 -->|so với| n43
  n1 -->|so với| n44
  n1 -->|so với| n45
  n1 -->|so với| n46
  n1 -->|so với| n47
  n1 -->|so với| n48
  n1 -->|so với| n49
  n1 -->|so với| n50
  n1 -->|so với| n51
  n1 -->|so với| n52
  n1 -->|so với| n53
  n1 -->|so với| n54
  n1 -->|so với| n55
  n1 -->|so với| n56
  n1 -->|so với| n57
  n1 -->|so với| n58
  n1 -->|so với| n59
  n1 -->|so với| n60
  n1 -->|so với| n61
  n1 -->|so với| n62
  n1 -->|so với| n63
  n1 -->|so với| n64
  n1 -->|so với| n65
  n1 -->|so với| n66
  n1 -->|so với| n67
  n1 -->|so với| n68
  n1 -->|so với| n69
  n1 -->|so với| n70
  n1 -->|so với| n71
  n1 -->|so với| n72
  n1 -->|so với| n73
  n1 -->|so với| n74
  n1 -->|so với| n75
  n1 -->|so với| n76
  n1 -->|so với| n77
  n1 -->|so với| n78
  n1 -->|so với| n79
  n1 -->|so với| n80
  n1 -->|so với| n81
  n1 -->|so với| n82
  n1 -->|so với| n83
  n1 -->|so với| n84
  n1 -->|so với| n85
  n1 -->|so với| n86
  n1 -->|so với| n87
  n1 -->|so với| n88
  n1 -->|so với| n89
  n1 -->|so với| n90
  n1 -->|so với| n91
  n1 -->|so với| n92
  n1 -->|so với| n93
  n1 -->|so với| n94
  n1 -->|so với| n95
  n1 -->|so với| n96
  n1 -->|so với| n97
  n1 -->|so với| n98
  n1 -->|so với| n99
  n1 -->|so với| n100
  n1 -->|so với| n101
  n1 -->|so với| n102
  n1 -->|so với| n103
  n1 -->|so với| n104
  n1 -->|so với| n105
  n1 -->|so với| n106
  n1 -->|so với| n107
  n1 -->|so với| n108
  n1 -->|so với| n109
  n1 -->|so với| n110
  n1 -->|so với| n111
  n1 -->|so với| n112
  n1 -->|so với| n113
  n1 -->|so với| n114
  n1 -->|so với| n115
  n1 -->|so với| n116
  n1 -->|so với| n117
  n1 -->|so với| n118
  n1 -->|so với| n119
  n1 -->|so với| n120
  n1 -->|so với| n121
  n1 -->|so với| n122
  n1 -->|so với| n123
  n1 -->|so với| n124
  n1 -->|so với| n125
  n1 -->|so với| n126
  n1 -->|so với| n127
  n1 -->|so với| n128
  n1 -->|so với| n129
  n1 -->|so với| n130
  n1 -->|so với| n131
  n1 -->|so với| n132
  n33 -->|chấm trên| n133
  n26 -->|chấm trên| n133
  n2 -->|chấm trên| n133
  n10 -->|chấm trên| n133
  n3 -->|chấm trên| n133
  n11 -->|chấm trên| n133
  n34 -->|chấm trên| n133
  n35 -->|chấm trên| n133
  n27 -->|chấm trên| n133
  n36 -->|chấm trên| n133
  n37 -->|chấm trên| n133
  n4 -->|chấm trên| n133
  n12 -->|chấm trên| n133
  n13 -->|chấm trên| n133
  n14 -->|chấm trên| n133
  n15 -->|chấm trên| n133
  n28 -->|chấm trên| n133
  n16 -->|chấm trên| n133
  n38 -->|chấm trên| n133
  n17 -->|chấm trên| n133
  n29 -->|chấm trên| n133
  n18 -->|chấm trên| n133
  n5 -->|chấm trên| n133
  n19 -->|chấm trên| n133
  n20 -->|chấm trên| n133
  n21 -->|chấm trên| n133
  n6 -->|chấm trên| n133
  n30 -->|chấm trên| n133
  n39 -->|chấm trên| n133
  n40 -->|chấm trên| n133
  n41 -->|chấm trên| n133
  n42 -->|chấm trên| n133
  n43 -->|chấm trên| n133
  n44 -->|chấm trên| n133
  n45 -->|chấm trên| n133
  n46 -->|chấm trên| n133
  n47 -->|chấm trên| n133
  n48 -->|chấm trên| n133
  n49 -->|chấm trên| n133
  n50 -->|chấm trên| n133
  n51 -->|chấm trên| n133
  n52 -->|chấm trên| n133
  n53 -->|chấm trên| n133
  n22 -->|chấm trên| n133
  n54 -->|chấm trên| n133
  n55 -->|chấm trên| n133
  n56 -->|chấm trên| n133
  n57 -->|chấm trên| n133
  n58 -->|chấm trên| n133
  n59 -->|chấm trên| n133
  n60 -->|chấm trên| n133
  n61 -->|chấm trên| n133
  n62 -->|chấm trên| n133
  n63 -->|chấm trên| n133
  n64 -->|chấm trên| n133
  n65 -->|chấm trên| n133
  n66 -->|chấm trên| n133
  n67 -->|chấm trên| n133
  n68 -->|chấm trên| n133
  n69 -->|chấm trên| n133
  n70 -->|chấm trên| n133
  n71 -->|chấm trên| n133
  n72 -->|chấm trên| n133
  n73 -->|chấm trên| n133
  n74 -->|chấm trên| n134
  n75 -->|chấm trên| n133
  n76 -->|chấm trên| n133
  n77 -->|chấm trên| n133
  n78 -->|chấm trên| n133
  n79 -->|chấm trên| n133
  n80 -->|chấm trên| n133
  n81 -->|chấm trên| n133
  n82 -->|chấm trên| n133
  n83 -->|chấm trên| n133
  n84 -->|chấm trên| n133
  n85 -->|chấm trên| n133
  n86 -->|chấm trên| n133
  n87 -->|chấm trên| n133
  n88 -->|chấm trên| n133
  n89 -->|chấm trên| n133
  n90 -->|chấm trên| n133
  n91 -->|chấm trên| n133
  n92 -->|chấm trên| n133
  n93 -->|chấm trên| n133
  n94 -->|chấm trên| n134
  n95 -->|chấm trên| n133
  n96 -->|chấm trên| n133
  n23 -->|chấm trên| n133
  n7 -->|chấm trên| n133
  n97 -->|chấm trên| n133
  n98 -->|chấm trên| n133
  n99 -->|chấm trên| n134
  n100 -->|chấm trên| n133
  n101 -->|chấm trên| n133
  n102 -->|chấm trên| n133
  n103 -->|chấm trên| n133
  n104 -->|chấm trên| n133
  n105 -->|chấm trên| n133
  n106 -->|chấm trên| n133
  n107 -->|chấm trên| n133
  n108 -->|chấm trên| n133
  n109 -->|chấm trên| n133
  n8 -->|chấm trên| n133
  n24 -->|chấm trên| n133
  n31 -->|chấm trên| n133
  n110 -->|chấm trên| n133
  n111 -->|chấm trên| n133
  n112 -->|chấm trên| n133
  n113 -->|chấm trên| n133
  n114 -->|chấm trên| n133
  n115 -->|chấm trên| n133
  n116 -->|chấm trên| n133
  n117 -->|chấm trên| n133
  n32 -->|chấm trên| n133
  n118 -->|chấm trên| n133
  n119 -->|chấm trên| n133
  n120 -->|chấm trên| n133
  n121 -->|chấm trên| n133
  n122 -->|chấm trên| n133
  n123 -->|chấm trên| n133
  n124 -->|chấm trên| n133
  n125 -->|chấm trên| n133
  n126 -->|chấm trên| n133
  n127 -->|chấm trên| n133
  n128 -->|chấm trên| n133
  n129 -->|chấm trên| n133
  n130 -->|chấm trên| n133
  n131 -->|chấm trên| n133
  n132 -->|chấm trên| n133
```
