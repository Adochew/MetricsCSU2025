import pandas as pd
import streamlit as st

def show_visualization(df, module):
    import plotly.express as px
    import plotly.graph_objects as go

    st.subheader("数据可视化")

    if module == "类图分析":
        # ==== 柱状图：每个类的 WMC ====
        wmc_col = "CK.WMC" if "CK.WMC" in df.columns else None
        if wmc_col:
            fig_bar = px.bar(df, x="NAME", y=wmc_col, title="每个类的 WMC（方法数）",
                             labels={"NAME": "类名", wmc_col: "WMC"}, height=400)
            st.plotly_chart(fig_bar, use_container_width=True)

        # ==== 雷达图：将所有类画在同一个图中 ====
        ck_cols = ["CK.WMC", "CK.DIT", "CK.NOC", "CK.CBO", "CK.RFC", "CK.LCOM"]
        available_cols = [col for col in ck_cols if col in df.columns]

        if available_cols:
            st.markdown("### 所有类的 CK 指标雷达图")

            fig_radar = go.Figure()

            for idx, row in df.iterrows():
                class_name = row["NAME"] if "NAME" in row else f"Class {idx}"
                radar_values = row[available_cols].values.tolist()
                radar_values.append(radar_values[0])  # 闭合曲线
                theta_labels = available_cols + [available_cols[0]]

                fig_radar.add_trace(go.Scatterpolar(
                    r=radar_values,
                    theta=theta_labels,
                    fill='none',
                    name=class_name
                ))

            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True)),
                title="各类的 CK 指标对比雷达图",
                showlegend=True
            )

            st.plotly_chart(fig_radar, use_container_width=True)

        # ==== 分组柱状图：LK 指标 ====
        lk_cols = ["LK.NOA", "LK.NOM", "LK.SIZE"]
        if all(col in df.columns for col in lk_cols):
            st.markdown("### 各类的 LK 指标分布（属性/方法/类大小）")
            fig_lk = px.bar(df, x="NAME", y=lk_cols,
                            title="每个类的 LK 指标（属性数/方法数/大小）",
                            labels={"value": "数量", "variable": "指标", "NAME": "类名"},
                            barmode="group")
            st.plotly_chart(fig_lk, use_container_width=True)

        # ==== 折线图：MOOD 指标趋势 ====
        mood_cols = ["MOOD.MHF", "MOOD.AHF", "MOOD.MIF", "MOOD.AIF", "MOOD.CF"]
        if any(col in df.columns for col in mood_cols):
            st.markdown("### 各类的 MOOD 指标趋势")

            fig_mood = px.line(df, x="NAME", y=mood_cols,
                               markers=True,
                               title="每个类的 MOOD 指标",
                               labels={"value": "值", "variable": "指标", "NAME": "类名"})
            st.plotly_chart(fig_mood, use_container_width=True)

        # ==== 热力图：类 vs CK 指标 ====
        ck_cols_full = ["CK.WMC", "CK.DIT", "CK.NOC", "CK.CBO", "CK.RFC", "CK.LCOM"]
        if all(col in df.columns for col in ck_cols_full):
            st.markdown("### CK 指标热力图（类 vs 指标）")

            heat_data = df.set_index("NAME")[ck_cols_full]
            fig_heat = px.imshow(heat_data,
                                 text_auto=True,
                                 aspect="auto",
                                 color_continuous_scale="YlGnBu",
                                 title="类 vs CK 指标 热力图")
            st.plotly_chart(fig_heat, use_container_width=True)



    elif module == "用例图分析":

        st.markdown("### 用例图关键指标分析")

        # === 柱状图 1：主要度量 ===
        fields1 = ["UAW", "UUCW", "UUCP", "UCP"]
        used1 = [f for f in fields1 if f in df.columns]

        if used1:
            values = df.loc[0, used1]
            fig1 = px.bar(x=used1, y=values, title="核心指标柱状图（用例点分析）", labels={"x": "指标", "y": "值"})
            st.plotly_chart(fig1, use_container_width=True)

        # === 饼图：参与者数 vs 用例数 ===
        if "ActorCount" in df.columns and "UseCaseCount" in df.columns:
            pie_data = pd.DataFrame({
                "类型": ["Actor", "UseCase"],
                "数量": [df.loc[0, "ActorCount"], df.loc[0, "UseCaseCount"]]
            })

            fig2 = px.pie(pie_data, names="类型", values="数量", title="参与者 vs 用例 数量比例")
            st.plotly_chart(fig2, use_container_width=True)

        # === 雷达图：复杂度因子 ===
        if "TCF" in df.columns and "EF" in df.columns:
            radar_data = {
                "指标": ["技术复杂度因子 (TCF)", "环境因子 (EF)", "调整后用例点 (UCP)"],
                "值": [df.loc[0, "TCF"], df.loc[0, "EF"], df.loc[0, "UCP"] / 100]  # 缩放UCP用于可视化
            }

            fig3 = go.Figure()
            fig3.add_trace(go.Scatterpolar(
                r=radar_data["值"] + [radar_data["值"][0]],
                theta=radar_data["指标"] + [radar_data["指标"][0]],
                fill='toself',
                name="复杂度因子"
            ))
            fig3.update_layout(
                polar=dict(radialaxis=dict(visible=True)),
                title="复杂度与环境因子雷达图（比例展示）",
                showlegend=False
            )
            st.plotly_chart(fig3, use_container_width=True)

    elif module == "代码指标分析":
        st.markdown("### 代码文件指标可视化")

        # --- 图1：每个文件的圈复杂度（总） ---
        if "File" in df.columns and "CyclomaticComplexity.Total" in df.columns:
            fig = px.bar(df, x="File", y="CyclomaticComplexity.Total",
                         title="每个文件的圈复杂度（总）",
                         labels={"File": "文件", "CyclomaticComplexity.Total": "复杂度总和"})
            st.plotly_chart(fig, use_container_width=True)

        # --- 图2：每个文件的函数数量 ---
        if "CyclomaticComplexity.FunctionCount" in df.columns:
            fig = px.bar(df, x="File", y="CyclomaticComplexity.FunctionCount",
                         title="每个文件的函数数量", labels={"CyclomaticComplexity.FunctionCount": "函数数"})
            st.plotly_chart(fig, use_container_width=True)

        # --- 图3：最大/平均复杂度并列图 ---
        if {"CyclomaticComplexity.Max", "CyclomaticComplexity.Avg"}.issubset(df.columns):
            fig = px.bar(df, x="File",
                         y=["CyclomaticComplexity.Max", "CyclomaticComplexity.Avg"],
                         title="每个文件的最大/平均圈复杂度",
                         labels={"value": "复杂度", "File": "文件", "variable": "类型"},
                         barmode="group")
            st.plotly_chart(fig, use_container_width=True)

        # --- 图4：行数组成结构堆叠图 ---
        line_cols = ["BlankLines", "CommentLines", "CodeLines"]
        if all(col in df.columns for col in line_cols):
            fig = px.bar(df, x="File", y=line_cols,
                         title="每个文件的代码结构（空行/注释/代码）",
                         labels={"value": "行数", "File": "文件", "variable": "类型"},
                         barmode="stack")
            st.plotly_chart(fig, use_container_width=True)
