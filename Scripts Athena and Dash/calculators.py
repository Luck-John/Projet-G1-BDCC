import pandas as pd

def calculate_moving_averages(df):
    """
    Calcule les Moyennes Mobiles sur 50 et 200 périodes (jours) pour l'analyse de tendance.
    La fonction utilise la méthode .rolling() de Pandas, appliquée par groupe de 'ticker'.
    """
    if df.empty:
        return df

    print("Démarrage du calcul des Moyennes Mobiles (MM50 et MM200)...")

    # Étape 1: Tri des données
    # Le calcul des MM DOIT se faire sur des données triées chronologiquement.
    df = df.sort_values(by=['ticker', 'transaction_date'])

    # Étape 2: Calcul des MM par groupe de Ticker
    # .transform() applique la fonction rolling() à chaque groupe et retourne une série 
    # de même longueur que le groupe, garantissant l'alignement correct.

    # Moyenne Mobile Courte (MM50)
    df['MM50'] = df.groupby('ticker')['close'].transform(
        lambda x: x.rolling(window=50, min_periods=1).mean()
    )

    # Moyenne Mobile Longue (MM200)
    df['MM200'] = df.groupby('ticker')['close'].transform(
        lambda x: x.rolling(window=200, min_periods=1).mean()
    )
    
    # -------------------------------------------------------------
    # 💡 BONUS : Calcule le rendement quotidien pour une analyse future
    # -------------------------------------------------------------
    df['Daily_Return'] = df.groupby('ticker')['close'].pct_change()
    
    print("Calculs terminés. MM50, MM200 et Daily_Return ajoutés au DataFrame.")
    
    return df