import streamlit as st
import pandas as pd
import random
import io

st.set_page_config(page_title="Kelebek Sınav Sistemi", layout="wide")

st.title("🦋 Kelebek Sınav Dağıtım Sistemi (Final)")
st.markdown("---")

st.sidebar.header("1. Ayarlar")
uploaded_file = st.sidebar.file_uploader("Öğrenci Listesi (Excel)", type=['xlsx'])

salon_sayisi = st.sidebar.number_input("Kaç Salon Var?", min_value=1, value=2)
salon_kapasiteleri = {}
for i in range(int(salon_sayisi)):
    salon_kapasiteleri[f"Salon {i+1}"] = st.sidebar.number_input(f"Salon {i+1} Kapasite", min_value=1, value=20)

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = [str(c).strip() for c in df.columns]
    sinif_col = next((c for c in ['Sınıf', 'Sınıfı', 'Sinif', 'SINIF'] if c in df.columns), None)

    if sinif_col is None:
        st.error(f"Excel'de 'Sınıf' sütunu bulunamadı!")
    else:
        if st.button("Mükemmel Dağıtımı Başlat"):
            gruplar = {s: df[df[sinif_col] == s].to_dict('records') for s in df[sinif_col].unique()}
            sinif_isimleri = list(gruplar.keys())
            
            karma_liste = []
            while any(gruplar.values()):
                random.shuffle(sinif_isimleri)
                for s_ad in sinif_isimleri:
                    if gruplar[s_ad]:
                        karma_liste.append(gruplar[s_ad].pop(0))

            salon_doluluk = {s: [] for s in salon_kapasiteleri.keys()}
            salon_isimleri = list(salon_kapasiteleri.keys())
            
            for ogrenci in karma_liste:
                uygun_salonlar = [s for s in salon_isimleri if len(salon_doluluk[s]) < salon_kapasiteleri[s]]
                if not uygun_salonlar: break
                
                secilen_salon = None
                uygun_salonlar.sort(key=lambda x: len(salon_doluluk[x]))
                
                for s in uygun_salonlar:
                    if not salon_doluluk[s] or salon_doluluk[s][-1][sinif_col] != ogrenci[sinif_col]:
                        secilen_salon = s
                        break
                if secilen_salon is None: secilen_salon = uygun_salonlar[0]
                salon_doluluk[secilen_salon].append(ogrenci)

            salon_sonuclari = {}
            islenen_toplam = 0
            tabs = st.tabs(list(salon_kapasiteleri.keys()))
            
            for i, (salon_adi, ogrenciler) in enumerate(salon_doluluk.items()):
                with tabs[i]:
                    if ogrenciler:
                        salon_df = pd.DataFrame(ogrenciler)
                        salon_df.insert(0, 'Sıra No', range(1, len(salon_df) + 1))
                        salon_df['Sınav Salonu'] = salon_adi
                        st.success(f"✅ {salon_adi}: {len(salon_df)} Öğrenci")
                        st.dataframe(salon_df, use_container_width=True)
                        salon_sonuclari[salon_adi] = salon_df
                        islenen_toplam += len(ogrenciler)

            if salon_sonuclari:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    for s_adi, s_df in salon_sonuclari.items():
                        s_df.to_excel(writer, sheet_name=s_adi, index=False)
                
                st.sidebar.markdown("---")
                st.sidebar.download_button(
                    label="📥 Mükemmel Listeyi İndir",
                    data=output.getvalue(),
                    file_name="kelebek_final_liste.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
else:
    st.info("💡 Lütfen Excel dosyasını yükleyin.")
