\* Source Pyomo model name=Model *\

min 
objective:
+0.10000000000000001 InvestmentFlow_invest(Meier_pv_b_Meier_el)
+3 InvestmentFlow_invest(b_Meier_el_Meier_heat_pump)
+10 flow(Meier_heat_pump_b_Meier_th_0)
+10 flow(Meier_heat_pump_b_Meier_th_1)
+2 flow(Meier_pv_b_Meier_el_0)
+2 flow(Meier_pv_b_Meier_el_1)
+0.27000000000000002 flow(b_el_net_transformer_to_Meier_el_0)
+0.27000000000000002 flow(b_el_net_transformer_to_Meier_el_1)
+1000 flow(shortage_el_b_el_net_0)
+1000 flow(shortage_el_b_el_net_1)

s.t.

c_e_Bus_balance(b_Meier_el_0)_:
+1 flow(Meier_pv_b_Meier_el_0)
-1 flow(b_Meier_el_Meier_heat_pump_0)
-1 flow(b_Meier_el_excess_Meier_el_0)
+1 flow(transformer_to_Meier_el_b_Meier_el_0)
= 0.8125406009560201

c_e_Bus_balance(b_Meier_el_1)_:
+1 flow(Meier_pv_b_Meier_el_1)
-1 flow(b_Meier_el_Meier_heat_pump_1)
-1 flow(b_Meier_el_excess_Meier_el_1)
+1 flow(transformer_to_Meier_el_b_Meier_el_1)
= 0.93620324997657844

c_e_Bus_balance(b_Meier_th_0)_:
+1 flow(Meier_heat_pump_b_Meier_th_0)
-1 flow(b_Meier_th_excess_Meier_th_0)
= 0.00054485047731748679

c_e_Bus_balance(b_Meier_th_1)_:
+1 flow(Meier_heat_pump_b_Meier_th_1)
-1 flow(b_Meier_th_excess_Meier_th_1)
= 0.00083499371868137127

c_e_Bus_balance(b_el_net_0)_:
-1 flow(b_el_net_excess_el_0)
-1 flow(b_el_net_transformer_to_Meier_el_0)
+1 flow(shortage_el_b_el_net_0)
= 0

c_e_Bus_balance(b_el_net_1)_:
-1 flow(b_el_net_excess_el_1)
-1 flow(b_el_net_transformer_to_Meier_el_1)
+1 flow(shortage_el_b_el_net_1)
= 0

c_e_Transformer_relation(Meier_heat_pump_b_Meier_el_b_Meier_th_0)_:
+0.0084067221628034341 flow(Meier_heat_pump_b_Meier_th_0)
+1 flow(b_Meier_el_Meier_heat_pump_0)
= 0

c_e_Transformer_relation(Meier_heat_pump_b_Meier_el_b_Meier_th_1)_:
-0.24391920112690424 flow(Meier_heat_pump_b_Meier_th_1)
+1 flow(b_Meier_el_Meier_heat_pump_1)
= 0

c_e_Transformer_relation(transformer_to_Meier_el_b_el_net_b_Meier_el_0)_:
+1 flow(b_el_net_transformer_to_Meier_el_0)
-1 flow(transformer_to_Meier_el_b_Meier_el_0)
= 0

c_e_Transformer_relation(transformer_to_Meier_el_b_el_net_b_Meier_el_1)_:
+1 flow(b_el_net_transformer_to_Meier_el_1)
-1 flow(transformer_to_Meier_el_b_Meier_el_1)
= 0

c_e_InvestmentFlow_fixed(Meier_pv_b_Meier_el_0)_:
-0.5 InvestmentFlow_invest(Meier_pv_b_Meier_el)
+1 flow(Meier_pv_b_Meier_el_0)
= 0

c_e_InvestmentFlow_fixed(Meier_pv_b_Meier_el_1)_:
-0.5 InvestmentFlow_invest(Meier_pv_b_Meier_el)
+1 flow(Meier_pv_b_Meier_el_1)
= 0

c_u_InvestmentFlow_max(Meier_pv_b_Meier_el_0)_:
-1 InvestmentFlow_invest(Meier_pv_b_Meier_el)
+1 flow(Meier_pv_b_Meier_el_0)
<= 0

c_u_InvestmentFlow_max(Meier_pv_b_Meier_el_1)_:
-1 InvestmentFlow_invest(Meier_pv_b_Meier_el)
+1 flow(Meier_pv_b_Meier_el_1)
<= 0

c_u_InvestmentFlow_max(b_Meier_el_Meier_heat_pump_0)_:
-1 InvestmentFlow_invest(b_Meier_el_Meier_heat_pump)
+1 flow(b_Meier_el_Meier_heat_pump_0)
<= 0

c_u_InvestmentFlow_max(b_Meier_el_Meier_heat_pump_1)_:
-1 InvestmentFlow_invest(b_Meier_el_Meier_heat_pump)
+1 flow(b_Meier_el_Meier_heat_pump_1)
<= 0

c_e_ONE_VAR_CONSTANT: 
ONE_VAR_CONSTANT = 1.0

bounds
   0 <= flow(Meier_heat_pump_b_Meier_th_0) <= +inf
   0 <= flow(Meier_heat_pump_b_Meier_th_1) <= +inf
   0 <= flow(Meier_pv_b_Meier_el_0) <= +inf
   0 <= flow(Meier_pv_b_Meier_el_1) <= +inf
   0 <= flow(b_Meier_el_Meier_heat_pump_0) <= +inf
   0 <= flow(b_Meier_el_Meier_heat_pump_1) <= +inf
   0 <= flow(b_Meier_el_excess_Meier_el_0) <= +inf
   0 <= flow(b_Meier_el_excess_Meier_el_1) <= +inf
   0 <= flow(b_Meier_th_excess_Meier_th_0) <= +inf
   0 <= flow(b_Meier_th_excess_Meier_th_1) <= +inf
   0 <= flow(b_el_net_excess_el_0) <= +inf
   0 <= flow(b_el_net_excess_el_1) <= +inf
   0 <= flow(b_el_net_transformer_to_Meier_el_0) <= +inf
   0 <= flow(b_el_net_transformer_to_Meier_el_1) <= +inf
   0 <= flow(shortage_el_b_el_net_0) <= +inf
   0 <= flow(shortage_el_b_el_net_1) <= +inf
   0 <= flow(transformer_to_Meier_el_b_Meier_el_0) <= +inf
   0 <= flow(transformer_to_Meier_el_b_Meier_el_1) <= +inf
   0 <= InvestmentFlow_invest(Meier_pv_b_Meier_el) <= +inf
   0 <= InvestmentFlow_invest(b_Meier_el_Meier_heat_pump) <= +inf
end
