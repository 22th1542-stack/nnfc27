import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from io import BytesIO

# =========================================================
# Page Setting
# =========================================================
st.set_page_config(
    page_title="CD Scatter Analysis System v1",
    page_icon="📊",
    layout="wide"
)

# =========================================================
# Style
# =========================================================
st.markdown("""
<style>
.main-title {
    font-size: 34px;
    font-weight: 800;
    color: #111827;
}
.sub-title {
    font-size: 15px;
    color: #6b7280;
    margin-bottom: 10px;
}
.section-card {
    background-color: #f9fafb;
    padding: 16px;
    border-radius: 14px;
    border: 1px solid #e5e7eb;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# Functions
# =========================================================
LOC_MAP = {
    "L": "Left",
    "B": "Bottom",
    "C": "Center",
    "T": "Top",
    "R": "Right"
}

POSITIONS = ["L", "B", "C", "T", "R"]

SYMBOLS = {
    "L": "triangle-left",
    "B": "triangle-down",
    "C": "circle",
    "T": "triangle-up",
    "R": "triangle-right"
}

def make_default_df(slot_count: int):
    return pd.DataFrame({
        "Slot": list(range(1, slot_count + 1)),
        "L": [np.nan] * slot_count,
        "B": [np.nan] * slot_count,
        "C": [np.nan] * slot_count,
        "T": [np.nan] * slot_count,
        "R": [np.nan] * slot_count,
    })

def calculate_stats(long_df, usl, lsl):
    values = long_df["CD"].dropna()

    if len(values) == 0:
        return {
            "mean": np.nan,
            "median": np.nan,
            "std": np.nan,
            "max": np.nan,
            "min": np.nan,
            "range": np.nan,
            "three_sigma": np.nan,
            "uniformity": np.nan,
            "cp": np.nan,
            "cpk": np.nan,
            "yield": np.nan,
            "pass_count": 0,
            "fail_count": 0
        }

    mean = values.mean()
    median = values.median()
    std = values.std(ddof=1) if len(values) > 1 else 0
    max_v = values.max()
    min_v = values.min()
    range_v = max_v - min_v
    three_sigma = 3 * std
    uniformity = ((max_v - min_v) / (2 * mean)) * 100 if mean != 0 else np.nan
    cp = (usl - lsl) / (6 * std) if std != 0 else np.nan
    cpk = min(usl - mean, mean - lsl) / (3 * std) if std != 0 else np.nan

    pass_count = int((long_df["Result"] == "Pass").sum())
    fail_count = int((long_df["Result"] == "Fail").sum())
    yield_rate = pass_count / len(long_df) * 100 if len(long_df) > 0 else np.nan

    return {
        "mean": mean,
        "median": median,
        "std": std,
        "max": max_v,
        "min": min_v,
        "range": range_v,
        "three_sigma": three_sigma,
        "uniformity": uniformity,
        "cp": cp,
        "cpk": cpk,
        "yield": yield_rate,
        "pass_count": pass_count,
        "fail_count": fail_count
    }

def draw_scatter(long_df, avg_df, target, usl, lsl, project, wafer_id):
    fig = go.Figure()

    for pos in POSITIONS:
        temp = long_df[long_df["Position"] == pos]

        if len(temp) == 0:
            continue

        colors = np.where(temp["Result"] == "Pass", "#2563eb", "#dc2626")

        fig.add_trace(go.Scatter(
            x=temp["Slot"],
            y=temp["CD"],
            mode="markers",
            name=f"{pos} ({LOC_MAP[pos]})",
            marker=dict(
                size=12,
                symbol=SYMBOLS[pos],
                color=colors,
                line=dict(color="black", width=1)
            ),
            text=[
                f"Slot {s}<br>Location {LOC_MAP[p]}<br>CD {c:.2f} nm<br>Result {r}"
                for s, p, c, r in zip(temp["Slot"], temp["Position"], temp["CD"], temp["Result"])
            ],
            hoverinfo="text"
        ))

    if len(avg_df) > 0:
        fig.add_trace(go.Scatter(
            x=avg_df["Slot"],
            y=avg_df["Avg"],
            mode="lines+markers",
            name="Average",
            line=dict(color="#111827", width=3),
            marker=dict(color="#111827", size=7)
        ))

    fig.add_hline(y=usl, line_dash="dash", line_color="red", annotation_text="USL")
    fig.add_hline(y=lsl, line_dash="dash", line_color="red", annotation_text="LSL")
    fig.add_hline(y=target, line_dash="dot", line_color="black", annotation_text="Target")

    fig.update_layout(
        height=620,
        template="plotly_white",
        title=f"{project} / {wafer_id} CD Scatter",
        xaxis_title="Slot",
        yaxis_title="CD Value (nm)",
        xaxis=dict(dtick=1),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.28,
            xanchor="center",
            x=0.5
        ),
        margin=dict(l=50, r=30, t=70, b=100)
    )

    return fig

def draw_box(long_df, target, usl, lsl):
    fig = go.Figure()

    for pos in POSITIONS:
        temp = long_df[long_df["Position"] == pos]

        fig.add_trace(go.Box(
            y=temp["CD"],
            name=f"{pos}<br>{LOC_MAP[pos]}",
            boxpoints="all",
            jitter=0.4,
            pointpos=0
        ))

    fig.add_hline(y=usl, line_dash="dash", line_color="red", annotation_text="USL")
    fig.add_hline(y=lsl, line_dash="dash", line_color="red", annotation_text="LSL")
    fig.add_hline(y=target, line_dash="dot", line_color="black", annotation_text="Target")

    fig.update_layout(
        height=620,
        template="plotly_white",
        title="Position별 CD Box Plot",
        yaxis_title="CD Value (nm)",
        margin=dict(l=50, r=30, t=70, b=60)
    )

    return fig

def fmt(value, unit=""):
    if value is None or pd.isna(value):
        return "-"
    return f"{value:.2f}{unit}"

# =========================================================
# Header
# =========================================================
st.markdown('<div class="main-title">CD Scatter Analysis System v1</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">LBCTR = Left / Bottom / Center / Top / Right 기반 Wafer Slot별 CD 산포 분석 Tool</div>', unsafe_allow_html=True)
st.divider()

# =========================================================
# Sidebar
# =========================================================
with st.sidebar:
    st.header("⚙ Setting")

    project = st.text_input("Project", "MIM Cap")
    wafer_id = st.text_input("Wafer ID", "Wafer_01")

    target = st.number_input("Target CD (nm)", value=500.0, step=1.0)
    margin = st.number_input("Spec Margin (%)", value=10.0, step=0.5)

    usl = target * (1 + margin / 100)
    lsl = target * (1 - margin / 100)

    st.write(f"USL : **{usl:.2f} nm**")
    st.write(f"LSL : **{lsl:.2f} nm**")

    slot_count = st.number_input("Slot Count", min_value=1, max_value=25, value=25)

    uploaded_file = st.file_uploader("Excel / CSV Upload", type=["xlsx", "csv"])

# =========================================================
# Data Load
# =========================================================
if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    for col in ["Slot"] + POSITIONS:
        if col not in df.columns:
            df[col] = np.nan

    df = df[["Slot"] + POSITIONS]

else:
    df = make_default_df(int(slot_count))

# =========================================================
# Main Layout
# =========================================================
left, right = st.columns([1.05, 1.45])

with left:
    st.subheader("📋 CD Data Input")
    st.caption("입력 순서: L = Left, B = Bottom, C = Center, T = Top, R = Right")

    edited_df = st.data_editor(
        df,
        use_container_width=True,
        num_rows="dynamic",
        hide_index=True,
        column_config={
            "Slot": st.column_config.NumberColumn("Slot", width="small", disabled=True),
            "L": st.column_config.NumberColumn("L", help="Left", width="small", format="%.2f"),
            "B": st.column_config.NumberColumn("B", help="Bottom", width="small", format="%.2f"),
            "C": st.column_config.NumberColumn("C", help="Center", width="small", format="%.2f"),
            "T": st.column_config.NumberColumn("T", help="Top", width="small", format="%.2f"),
            "R": st.column_config.NumberColumn("R", help="Right", width="small", format="%.2f"),
        },
        key="cd_input_table"
    )

    edited_df["Avg"] = edited_df[POSITIONS].mean(axis=1)

    st.subheader("📌 Slot Average")
    st.dataframe(
        edited_df[["Slot", "Avg"]],
        use_container_width=True,
        hide_index=True
    )

# =========================================================
# Long Data
# =========================================================
long_df = edited_df.melt(
    id_vars=["Slot"],
    value_vars=POSITIONS,
    var_name="Position",
    value_name="CD"
)

long_df = long_df.dropna(subset=["CD"])

long_df["Location"] = long_df["Position"].map(LOC_MAP)

long_df["Result"] = np.where(
    (long_df["CD"] >= lsl) & (long_df["CD"] <= usl),
    "Pass",
    "Fail"
)

avg_df = edited_df.dropna(subset=["Avg"])

stats = calculate_stats(long_df, usl, lsl)

# =========================================================
# Plot Area
# =========================================================
with right:
    tab1, tab2 = st.tabs(["📈 Scatter Plot", "📦 Box Plot"])

    with tab1:
        scatter_fig = draw_scatter(
            long_df=long_df,
            avg_df=avg_df,
            target=target,
            usl=usl,
            lsl=lsl,
            project=project,
            wafer_id=wafer_id
        )
        st.plotly_chart(scatter_fig, use_container_width=True)

    with tab2:
        if len(long_df) > 0:
            box_fig = draw_box(long_df, target, usl, lsl)
            st.plotly_chart(box_fig, use_container_width=True)
        else:
            st.info("CD 데이터를 입력하면 Box Plot이 표시됩니다.")

# =========================================================
# Summary
# =========================================================
st.divider()
st.subheader("📊 Summary Statistics")

m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("Mean", fmt(stats["mean"], " nm"))
m2.metric("Std", fmt(stats["std"]))
m3.metric("3σ", fmt(stats["three_sigma"]))
m4.metric("Cpk", fmt(stats["cpk"]))
m5.metric("Uniformity", fmt(stats["uniformity"], " %"))
m6.metric("Yield", fmt(stats["yield"], " %"))

m7, m8, m9, m10, m11, m12 = st.columns(6)
m7.metric("Max", fmt(stats["max"], " nm"))
m8.metric("Min", fmt(stats["min"], " nm"))
m9.metric("Range", fmt(stats["range"], " nm"))
m10.metric("Cp", fmt(stats["cp"]))
m11.metric("Pass", stats["pass_count"])
m12.metric("Fail", stats["fail_count"])

# =========================================================
# Capability Judgment
# =========================================================
st.subheader("🧠 Process Capability Judgment")

cpk = stats["cpk"]

if pd.isna(cpk):
    st.info("CD 데이터를 입력하면 Cpk 판단이 표시됩니다.")
else:
    if cpk >= 1.67:
        st.success(f"Cpk = {cpk:.2f} → 매우 안정적인 공정 수준입니다.")
    elif cpk >= 1.33:
        st.info(f"Cpk = {cpk:.2f} → 양산 가능 수준입니다.")
    elif cpk >= 1.00:
        st.warning(f"Cpk = {cpk:.2f} → 공정 관리가 필요합니다.")
    else:
        st.error(f"Cpk = {cpk:.2f} → 산포 개선이 필요합니다.")

# =========================================================
# Spec-Out Table
# =========================================================
st.divider()
st.subheader("🚨 Spec-Out Data")

fail_df = long_df[long_df["Result"] == "Fail"][["Slot", "Position", "Location", "CD", "Result"]]

if len(fail_df) > 0:
    st.dataframe(
        fail_df.style.applymap(
            lambda x: "color: red; font-weight: bold;" if x == "Fail" else "",
            subset=["Result"]
        ),
        use_container_width=True,
        hide_index=True
    )
else:
    st.success("현재 Spec-Out Data가 없습니다.")

# =========================================================
# Excel Export
# =========================================================
st.divider()
st.subheader("📥 Excel Export")

summary_df = pd.DataFrame({
    "Item": [
        "Project", "Wafer ID", "Target CD", "USL", "LSL",
        "Mean", "Median", "Std", "3 Sigma", "Cp", "Cpk",
        "Uniformity (%)", "Max", "Min", "Range", "Yield (%)",
        "Pass Count", "Fail Count"
    ],
    "Value": [
        project, wafer_id, target, usl, lsl,
        stats["mean"], stats["median"], stats["std"], stats["three_sigma"],
        stats["cp"], stats["cpk"], stats["uniformity"],
        stats["max"], stats["min"], stats["range"], stats["yield"],
        stats["pass_count"], stats["fail_count"]
    ]
})

output = BytesIO()

with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
    edited_df.to_excel(writer, index=False, sheet_name="Input_Data")
    long_df.to_excel(writer, index=False, sheet_name="Long_Data")
    fail_df.to_excel(writer, index=False, sheet_name="Spec_Out")
    summary_df.to_excel(writer, index=False, sheet_name="Summary")

st.download_button(
    label="Excel Result Download",
    data=output.getvalue(),
    file_name=f"{project}_{wafer_id}_CD_Result.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
