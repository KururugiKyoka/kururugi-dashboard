import pandas as pd
from fredapi import Fred
import datetime
import os

# --- 設定 ---
# 1. ここにFREDで取得したAPIキーを貼り付けてください
# キーの取得はこちら：https://fred.stlouisfed.org/docs/api/api_key.html
FRED_API_KEY = 'a47b337813557ea08a86f8fd5c50415c'
fred = Fred(api_key=FRED_API_KEY)

def fetch_canary_data():
    print("🚀 FREDから最新の『カナリア』データを取得中...")
    
    # 監視する代表的な指標（FREDコード）
    metrics = {
        '10Y2Y_Spread': 'T10Y2Y',       # 長短金利差 (金融市場の先行指標)
        'HY_Spread': 'BAMLH0A0HYM2',    # ハイイールド債スプレッド (企業の信用リスク)
        'Initial_Claims': 'ICSA',       # 新規失業保険申請件数 (労働市場の亀裂)
        'Truck_Sales': 'HTRUCKSSAAR'    # 大型トラック販売台数 (実体経済・投資)
    }
    
    df_list = []
    
    for name, code in metrics.items():
        try:
            series = fred.get_series(code)
            df_list.append(pd.DataFrame({name: series}))
        except Exception as e:
            print(f"❌ {name} の取得に失敗しました: {e}")
        
    if not df_list:
        print("⚠️ データが一つも取得できませんでした。APIキーを確認してください。")
        return

    # データを結合し、欠損値を前の値で補完
    df_final = pd.concat(df_list, axis=1).ffill().dropna()
    
    # 直近3年分（約1100日）に絞り込み
    start_date = datetime.datetime.now() - datetime.timedelta(days=3*365)
    df_final = df_final[df_final.index >= start_date]
    
    # CSVファイルとして保存
    df_final.to_csv('canary_data.csv')
    print(f"✨ 成功: canary_data.csv に {len(df_final)} 件のデータを保存しました。")

if __name__ == "__main__":
    fetch_canary_data()
