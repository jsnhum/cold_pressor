import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import io

# Sätt sidans konfiguration
st.set_page_config(
    page_title="Cold Press Experiment",
    page_icon="❄️",
    layout="wide"
)

# Titel och beskrivning
st.title("Cold Pressor Experiment - Smärttolerans")
st.markdown("""
Denna app hjälper dig att samla in och analysera data från Cold Pressor-experimentet 
där smärttolerans mäts genom att mäta tiden deltagare kan hålla sin hand i kallt vatten (1°C).

**Instruktioner:**
1. Fyll i deltagarinformation (deltagarens nummer, kön och tid i sekunder)
2. Klicka på 'Lägg till data' för att registrera deltagaren
3. Fortsätt tills alla deltagare är registrerade
4. Exportera data som CSV-fil om du vill spara resultaten
5. Analysera data med t-test för att jämföra skillnader mellan män och kvinnor
""")

# Initiera dataframe i session state om den inte finns
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["Deltagare", "Kön", "Tid (s)"])
    # Sätt datatyperna explicit
    st.session_state.data = st.session_state.data.astype({"Deltagare": int, "Kön": str, "Tid (s)": float})
    st.session_state.counter = 1

# Funktion för att lägga till data
def add_data():
    # Validera data
    if gender == "" or time_sec < 0 or time_sec > 300:
        st.error("Vänligen kontrollera inmatad data. Tid måste vara mellan 0 och 300 sekunder.")
        return
    
    # Lägg till i dataframe
    new_data = pd.DataFrame({
        "Deltagare": [st.session_state.counter],
        "Kön": [gender],
        "Tid (s)": [float(time_sec)]  # Explicit konvertering till float
    })
    
    st.session_state.data = pd.concat([st.session_state.data, new_data], ignore_index=True)
    st.session_state.counter += 1
    st.success(f"Data för deltagare {st.session_state.counter-1} har lagts till!")

# Funktion för att återställa data
def reset_data():
    st.session_state.data = pd.DataFrame(columns=["Deltagare", "Kön", "Tid (s)"])
    # Sätt datatyperna explicit
    st.session_state.data = st.session_state.data.astype({"Deltagare": int, "Kön": str, "Tid (s)": float})
    st.session_state.counter = 1
    st.success("All data har återställts!")

# Funktion för att utföra t-test
def perform_ttest(df):
    if len(df) < 2:
        st.warning("För få deltagare för att utföra statistisk analys.")
        return None, None, None, None
    
    # Säkerställ att data är numerisk
    df["Tid (s)"] = pd.to_numeric(df["Tid (s)"])
    
    # Skapa grupper baserade på kön
    male_data = df[df["Kön"] == "Man"]["Tid (s)"].values
    female_data = df[df["Kön"] == "Kvinna"]["Tid (s)"].values
    
    # Kontrollera om vi har data för båda könen
    if len(male_data) == 0 or len(female_data) == 0:
        st.warning("Data saknas för ett eller båda könen.")
        return None, None, None, None
    
    # Utför t-test
    t_stat, p_val = stats.ttest_ind(male_data, female_data, equal_var=False)
    
    # Beräkna medelvärden och standardavvikelser
    male_mean = male_data.mean()
    female_mean = female_data.mean()
    male_std = male_data.std()
    female_std = female_data.std()
    
    return t_stat, p_val, {
        "Man": {"Medelvärde": male_mean, "Standardavvikelse": male_std, "Antal": len(male_data)},
        "Kvinna": {"Medelvärde": female_mean, "Standardavvikelse": female_std, "Antal": len(female_data)}
    }, {"Man": male_data, "Kvinna": female_data}

# Funktion för att skapa boxplot
def create_boxplot(data_dict):
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Skapa dataframe för plotting
    plot_data = []
    labels = []
    
    for gender, times in data_dict.items():
        for time in times:
            plot_data.append(time)
            labels.append(gender)
    
    plot_df = pd.DataFrame({"Kön": labels, "Tid (s)": plot_data})
    
    # Skapa boxplot med seaborn
    sns.boxplot(x="Kön", y="Tid (s)", data=plot_df, ax=ax)
    sns.stripplot(x="Kön", y="Tid (s)", data=plot_df, color="black", alpha=0.5, ax=ax)
    
    plt.title("Jämförelse av smärttolerans mellan män och kvinnor")
    plt.ylabel("Tid (sekunder)")
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    return fig

# Funktion för att skapa barplot
def create_barplot(stats_dict):
    fig, ax = plt.subplots(figsize=(10, 6))
    
    genders = list(stats_dict.keys())
    means = [stats_dict[g]["Medelvärde"] for g in genders]
    stds = [stats_dict[g]["Standardavvikelse"] for g in genders]
    
    # Skapa barplot
    bars = ax.bar(genders, means, yerr=stds, capsize=10, color=['skyblue', 'lightpink'])
    
    plt.title("Genomsnittlig smärttolerans med standardavvikelse")
    plt.ylabel("Tid (sekunder)")
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Lägg till värden på staplarna
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 5,
                f'{height:.1f}',
                ha='center', va='bottom')
    
    return fig

# Layout för inmatningsformulär
st.header("Registrera data")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Deltagare #" + str(st.session_state.counter))

with col2:
    gender = st.radio("Kön", ["Man", "Kvinna"], horizontal=True)

with col3:
    time_sec = st.number_input("Tid (sekunder)", 
                               min_value=0, 
                               max_value=300, 
                               value=0,
                               help="Ange hur länge deltagaren höll handen i vattnet (max 300 sekunder)")

col1, col2 = st.columns(2)
with col1:
    st.button("Lägg till data", on_click=add_data)
with col2:
    st.button("Återställ all data", on_click=reset_data)

# Visa insamlad data
st.header("Insamlad data")

if not st.session_state.data.empty:
    st.dataframe(st.session_state.data, use_container_width=True)
    
    # Export av data
    csv = st.session_state.data.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Ladda ner data som CSV",
        data=csv,
        file_name='cold_press_data.csv',
        mime='text/csv',
    )
    
    # Statistisk analys
    st.header("Statistisk analys")
    
    t_stat, p_val, stats_dict, data_dict = perform_ttest(st.session_state.data)
    
    if t_stat is not None:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Deskriptiv statistik")
            
            # Skapa tabell för deskriptiv statistik
            stats_table = pd.DataFrame({
                "Kön": ["Man", "Kvinna"],
                "Antal": [stats_dict["Man"]["Antal"], stats_dict["Kvinna"]["Antal"]],
                "Medelvärde (s)": [round(stats_dict["Man"]["Medelvärde"], 2), 
                                round(stats_dict["Kvinna"]["Medelvärde"], 2)],
                "Standardavvikelse": [round(stats_dict["Man"]["Standardavvikelse"], 2), 
                                    round(stats_dict["Kvinna"]["Standardavvikelse"], 2)]
            })
            
            st.table(stats_table)
        
        with col2:
            st.subheader("T-test resultat")
            st.write(f"**t-värde:** {t_stat:.4f}")
            st.write(f"**p-värde:** {p_val:.4f}")
            
            if p_val < 0.05:
                st.success(f"Signifikant skillnad hittades mellan män och kvinnor (p < 0.05)")
            else:
                st.info(f"Ingen signifikant skillnad hittades mellan män och kvinnor (p > 0.05)")
        
        # Skapa visualiseringar
        st.subheader("Visualisering av resultat")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.pyplot(create_boxplot(data_dict))
        
        with col2:
            st.pyplot(create_barplot(stats_dict))
else:
    st.info("Ingen data har registrerats ännu. Använd formuläret ovan för att lägga till data.")

# Lägga till instruktioner i sidebaren
st.sidebar.title("Om experimentet")
st.sidebar.markdown("""
### Cold Pressor Experiment

Detta experiment undersöker smärttolerans genom att mäta hur länge deltagare kan hålla handen i iskallt vatten (1°C).

**Observera:**
- Varje deltagare kan max hålla handen i vattnet i 5 minuter (300 sekunder)
- Experimentet bör genomföras med jämn könsfördelning (ca 5 män och 5 kvinnor)
- Deltagare kan avbryta experimentet när som helst

**Frågeställning:**
Skiljer sig tiden som handen kan hållas i det kalla vattnet åt mellan män respektive kvinnor?

För mer information, se laborationsinstruktionerna.
""")

# Footer
st.markdown("---")
st.caption("Cold Press Experiment - Laboration i smärttolerans")