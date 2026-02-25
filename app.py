import streamlit as st
import pandas as pd
import random
import io

st.set_page_config(page_title="Kelebek Sınav Sistemi", layout="wide")

st.title("🦋 Kelebek Sınav Sistemi (Kademeli Dağıtım: 5-6 ve 7-8)")
st.info("Bu sürüm 5-6. sınıfları kendi içinde, 7-8. sınıfları kendi içinde dağıtır.")

st.sidebar.header("1. Ayarlar")
uploaded_file = st.sidebar.file_uploader("Öğrenci Listesi (Excel)", type=['xlsx'])

salon_sayisi = st.sidebar.number_input("Toplam Kaç Salon Var?", min_value=1, value=24)
varsayilan_kapasite = st.sidebar.number_input("Varsayılan Salon Kapasitesi", min_value=1, value=32)

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = [str(c).strip() for c in df.columns]
    
    # Sınıf sütununu bul
    sinif_col = next((c for c in ['Sınıf', 'Sınıfı', 'Sinif', 'SINIF', 'SINIF-ŞUBE'] if c in df.columns), None)

    if sinif_col is None:
        st.error(f"Excel'de 'Sınıf' sütunu bulunamadı!")
    else:
        # --- GRUPLANDIRMA MANTIĞI ---
        # Sınıfın ilk karakterine bakarak 5-6 ve 7-8 ayrımı yapıyoruz
        df['Grup'] = df[sinif_col].apply(lambda x: "5-6" if str(x)[0] in ['5', '6'] else "7-8")
        
        grup_56 = df[df['Grup'] == "5-6"].copy()
        grup_78 = df[df['Grup'] == "7-8"].copy()
        
        st.sidebar.write(f"📊 5-6 Grubu: {len(grup_56)} öğrenci")
        st.sidebar.write(f"📊 7-8 Grubu: {len(grup_78)} öğrenci")

        if st.button("Kademeli Dağıtımı Başlat"):
            def kelebek_karistir(veriseti):
                """Bir grubu kendi içinde şubelere göre karıştırır."""
                subeler = veriseti[sinif_col].unique()
                gruplar = {s: veriseti[veriseti[sinif_col] == s].to_dict('records') for s in subeler}
                karma = []
                while any(gruplar.values()):
                    s_list = list(gruplar.keys())
                    random.shuffle(s_list)
                    for s in s_list:
                        if gruplar[s]:
                            karma.append(gruplar[s].pop(0))
                return karma

            # Her grubu kendi içinde karıştır
            karma_56 = kelebek_karistir(grup_56)
            karma_78 = kelebek_karistir(grup_78)

            # --- SALONLARI PAYLAŞTIR ---
            # Toplam öğrenciye göre 5-6 grubu kaç salon kaplıyor hesapla
            oran_56 = len(grup_56) / len(df)
            salon_siniri = round(salon_sayisi * oran_56)
            
            salonlar_56 = [f"Salon {i+1}" for i in range(salon_siniri)]
            salonlar_78 = [f"Salon {i+1}" for i in range(salon_siniri, int(salon_sayisi))]
            
            st.write(f"📍 {len(salonlar_56)} Salon 5-6 grubuna, {len(salonlar_78)} Salon 7-8 grubuna ayrıldı.")

            def dagit(ogrenciler, salon_adlari):
                doluluk = {s: [] for s in salon_adlari}
                for ogrenci in ogrenciler:
                    uygun = [s for s in salon_adlari if len(doluluk[s]) < varsayilan_kapasite]
                    if not uygun: break
                    
                    # Denge için en boş salonu seç
                    uygun.sort(key=lambda x: len(doluluk[x]))
                    
                    secilen = None
                    for s in uygun:
                        if not doluluk[s] or doluluk[s][-1][sinif_col] != ogrenci[sinif_col]:
                            secilen = s
                            break
                    if not secilen: secilen = uygun[0]
                    doluluk[secilen].append(ogrenci)
                return doluluk

            sonuc_56 = dagit(karma_56, salonlar_56)
            sonuc_78 = dagit(karma_78, salonlar_78)
            
            # Sonuçları birleştir
            tum_sonuclar = {**sonuc_56, **sonuc_78}
            
            # --- EKRANA BASMA VE EXCEL ---
            tabs = st.tabs(list(tum_sonuclari.keys()))
            salon_dfs = {}
            for i, (s_adi, ogrenciler) in enumerate(tum_sonuclari.items()):
                with tabs[i]:
                    if ogrenciler:
                        s_df = pd.DataFrame(ogrenciler)
                        s_df.insert(0, 'Sıra No', range(1, len(s_df) + 1))
                        st.dataframe(s_df)
                        salon_dfs[s_adi] = s_df
                    else:
                        st.warning("Bu salon boş kaldı.")

            if salon_dfs:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    for s_adi, s_df in salon_dfs.items():
                        s_df.to_excel(writer, sheet_name=s_adi, index=False)
                
                st.sidebar.download_button("📥 Kademeli Listeyi İndir", output.getvalue(), "kelebek_kademeli.xlsx")
