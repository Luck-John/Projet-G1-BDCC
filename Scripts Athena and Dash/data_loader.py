import pandas as pd
from pyathena import connect
from dotenv import load_dotenv
import os
import warnings
from calculators import calculate_moving_averages

# --- 1. CHARGEMENT DES VARIABLES D'ENVIRONNEMENT ---
# Assurez-vous d'avoir un fichier .env à la racine de votre projet avec vos clés AWS
load_dotenv() 

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "eu-west-3") # Valeur par défaut si non trouvé
S3_STAGING_DIR = os.getenv("S3_STAGING_DIR")

# --- 2. DÉFINITION DE LA REQUÊTE SQL ---
# Utilisation de la colonne "close" au lieu de "adj_close" tant que le problème n'est pas résolu
SQL_QUERY = """
SELECT
    ticker,
    "close",
    -- On convertit le timestamp en Date/Heure lisible, puis on tronque à la date pour l'agrégation
    DATE(from_unixtime(CAST(datetime AS DECIMAL) / 1000000000)) AS transaction_date
FROM
    "finance_data_lake_db"."curated_prices"
WHERE
    -- Cette clause est cruciale pour la performance. Limitez la période à ce dont vous avez besoin.
    DATE(from_unixtime(CAST(datetime AS DECIMAL) / 1000000000)) > date '2023-01-01'
"""

def get_data_from_athena():
    """
    Se connecte à Athena et exécute la requête SQL.
    Retourne un DataFrame Pandas contenant les données brutes.
    """
    if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_STAGING_DIR]):
        raise EnvironmentError(
            "Veuillez vérifier que les variables AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY et S3_STAGING_DIR "
            "sont bien définies dans votre fichier .env."
        )

    try:
        # Établissement de la connexion
        conn = connect(
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION,
            s3_staging_dir=S3_STAGING_DIR
        )
        
        # Exécution de la requête et chargement dans Pandas
        df = pd.read_sql(SQL_QUERY, conn)
        
        # Nettoyage initial des types de données
        df['transaction_date'] = pd.to_datetime(df['transaction_date'])
        # Le paramètre errors='coerce' transformera les données non numériques en NaN
        df['close'] = pd.to_numeric(df['close'], errors='coerce') 

        return df

    except Exception as e:
        print(f"Échec de la connexion ou de l'exécution de la requête Athena. Détails: {e}")
        return pd.DataFrame()


def load_data():
    """
    Fonction principale appelée par app.py.
    Elle gère le pipeline complet : Extraction -> Transformation/Calculs.
    """
    warnings.filterwarnings('ignore', category=pd.errors.PerformanceWarning)

    df_raw = get_data_from_athena()
    
    if df_raw.empty:
        return pd.DataFrame()
    
    # Appel des fonctions de calculs pour enrichir le DataFrame
    df_final = calculate_moving_averages(df_raw)
    
    return df_final

# Exemple d'utilisation (décommenter pour tester ce fichier indépendamment)
# if __name__ == '__main__':
#     data = load_data()
#     print(data.head())
#     print(data.info())