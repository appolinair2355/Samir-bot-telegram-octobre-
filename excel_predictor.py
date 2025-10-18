"""
Excel-based prediction system for Telegram Bot
Reads predictions from an Excel file instead of using mirror rules
"""

import logging
import os
import re
from typing import Optional, Tuple, List, Dict, Any
from openpyxl import load_workbook
from datetime import datetime

logger = logging.getLogger(__name__)

class ExcelPredictor:
    """Handles Excel-based predictions"""

    def __init__(self, excel_file_path: str = "predictions.xlsx"):
        self.excel_file_path = excel_file_path
        self.predictions_data: List[Dict] = []
        self.last_loaded_time: Optional[datetime] = None
        self.load_predictions()

    def load_predictions(self) -> bool:
        """Load predictions from Excel file"""
        try:
            if not os.path.exists(self.excel_file_path):
                logger.warning(f"⚠️ Fichier Excel non trouvé: {self.excel_file_path}")
                logger.info(f"💡 Créez un fichier {self.excel_file_path} avec les colonnes: Numero, Costume")
                return False

            workbook = load_workbook(self.excel_file_path, data_only=True)
            sheet = workbook.active

            self.predictions_data = []

            headers = [cell.value for cell in sheet[1]]
            logger.info(f"📊 En-têtes Excel: {headers}")

            numero_col = None
            costume_col = None

            for idx, header in enumerate(headers):
                header_lower = str(header).lower()
                # Reconnaître la colonne Numero (ancien et nouveau format)
                if header_lower and ('numero' in header_lower or 'numéro' in header_lower):
                    numero_col = idx
                # Reconnaître la colonne Costume (ancien et nouveau format)
                if header_lower and ('costume' in header_lower or 'première couleur' in header_lower or 'premiere couleur' in header_lower or 'couleur' in header_lower):
                    costume_col = idx

            if numero_col is None or costume_col is None:
                logger.error(f"❌ Colonnes 'Numero' et 'Costume' non trouvées dans le fichier Excel")
                return False

            for row in sheet.iter_rows(min_row=2, values_only=True):
                if row[numero_col] is not None:
                    try:
                        numero = int(row[numero_col])
                        costume_text = str(row[costume_col]).strip().lower() if row[costume_col] else ""

                        costume_emoji = self._text_to_costume(costume_text)

                        if costume_emoji:
                            self.predictions_data.append({
                                'numero': numero,
                                'costume': costume_emoji,
                                'costume_text': costume_text
                            })
                            logger.info(f"✅ Prédiction chargée: N{numero} → {costume_emoji} ({costume_text})")
                    except (ValueError, TypeError) as e:
                        logger.warning(f"⚠️ Ligne ignorée (format invalide): {row} - {e}")

            self.predictions_data.sort(key=lambda x: x['numero'])
            self.last_loaded_time = datetime.now()

            logger.info(f"📊 {len(self.predictions_data)} prédictions chargées depuis {self.excel_file_path}")
            return True

        except Exception as e:
            logger.error(f"❌ Erreur lors du chargement du fichier Excel: {e}")
            return False

    def _text_to_costume(self, costume_text: str) -> Optional[str]:
        """Convert text costume to emoji"""
        costume_map = {
            'pique': '♠️',
            'coeur': '♥️',
            'cœur': '♥️',  # Ajout du oe français
            'carreau': '♦️',
            'trèfle': '♣️',
            'trefle': '♣️',
            'trефle': '♣️',
            '♠️': '♠️',
            '♥️': '♥️',
            '❤️': '♥️',
            '♦️': '♦️',
            '♣️': '♣️',
            'spade': '♠️',
            'heart': '♥️',
            'diamond': '♦️',
            'club': '♣️'
        }

        # Normaliser le texte pour gérer différents encodages
        normalized_text = costume_text.lower().strip()
        
        for key, value in costume_map.items():
            if key in normalized_text:
                return value

        logger.warning(f"⚠️ Costume non reconnu: {costume_text}")
        return None

    def find_next_prediction(self, current_game_number: int, max_distance: int = 2) -> Optional[Tuple[int, str]]:
        """
        Find the next prediction to make based on current game number
        Returns (game_number, costume) if a prediction should be made, None otherwise

        Args:
            current_game_number: The current game number from the source channel
            max_distance: Maximum distance to look ahead (default 2, changé de 3)
        """
        if not self.predictions_data:
            logger.warning("⚠️ Aucune prédiction chargée depuis Excel")
            return None

        for prediction in self.predictions_data:
            target_numero = prediction['numero']
            distance = target_numero - current_game_number

            if 0 <= distance <= max_distance:
                logger.info(f"🎯 PRÉDICTION TROUVÉE: Jeu actuel N{current_game_number}, "
                          f"Prédiction pour N{target_numero} ({prediction['costume']}) - Distance: {distance}")
                return (target_numero, prediction['costume'])

        return None

    def remove_prediction(self, game_number: int) -> bool:
        """Remove a prediction after it has been made"""
        initial_count = len(self.predictions_data)
        self.predictions_data = [p for p in self.predictions_data if p['numero'] != game_number]
        removed = initial_count > len(self.predictions_data)

        if removed:
            logger.info(f"🗑️ Prédiction N{game_number} retirée de la liste")

        return removed

    def reload_if_modified(self) -> bool:
        """Reload predictions file if it has been modified"""
        try:
            if not os.path.exists(self.excel_file_path):
                return False

            file_modified_time = datetime.fromtimestamp(os.path.getmtime(self.excel_file_path))

            if self.last_loaded_time is None or file_modified_time > self.last_loaded_time:
                logger.info(f"🔄 Fichier Excel modifié, rechargement...")
                return self.load_predictions()

            return False
        except Exception as e:
            logger.error(f"❌ Erreur lors de la vérification du fichier: {e}")
            return False

    def get_all_predictions(self) -> List[Dict]:
        """Get all loaded predictions"""
        return self.predictions_data.copy()

    def get_stats(self) -> Dict:
        """Get statistics about loaded predictions"""
        return {
            'total_predictions': len(self.predictions_data),
            'last_loaded': self.last_loaded_time.strftime('%Y-%m-%d %H:%M:%S') if self.last_loaded_time else 'Never',
            'file_exists': os.path.exists(self.excel_file_path),
            'file_path': self.excel_file_path
        }

    def check_and_predict(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Check if we should make a prediction based on the current message
        Returns (should_predict, prediction_message)
        """
        try:
            # Extract game number from text (format: #n123)
            match = re.search(r'#n(\d+)', text.lower())
            if not match:
                return False, None

            current_game = int(match.group(1))
            logger.info(f"🎮 Jeu actuel détecté: #n{current_game}")

            # Check if message has completion indicators (skip if it's a result)
            if '🔰' in text or '✅' in text:
                logger.info(f"⏭️ Message de résultat ignoré pour prédiction Excel")
                return False, None

            # Find predictions within distance 0-2 (changé de 0-3 à 0-2)
            predictions_to_make = []
            for prediction in self.predictions_data:
                target_numero = prediction['numero']
                distance = target_numero - current_game
                if 0 <= distance <= 2:
                    predictions_to_make.append((target_numero, prediction, distance))
                    logger.info(f"🎯 Prédiction trouvée: N{target_numero} (distance: {distance})")

            if not predictions_to_make:
                return False, None

            # Sort by distance and take the closest one
            predictions_to_make.sort(key=lambda x: x[2])
            pred_num, pred_data, distance = predictions_to_make[0]

            # Create prediction message with new format: 🔵42🔵:♠️statut :⏳
            costume_emoji = pred_data['costume']
            prediction_message = f"🔵{pred_num}🔵:{costume_emoji}statut :⏳"

            # Remove this prediction from the list
            self.predictions_data = [p for p in self.predictions_data if p['numero'] != pred_num]
            logger.info(f"✅ Prédiction N{pred_num} retirée de la liste (reste {len(self.predictions_data)})")

            return True, prediction_message

        except Exception as e:
            logger.error(f"❌ Erreur dans check_and_predict: {e}")
            return False, None

    def _get_costume_name(self, emoji: str) -> str:
        """Get costume name from emoji"""
        costume_map = {
            '♠️': 'Pique',
            '♥️': 'Cœur',
            '♦️': 'Carreau',
            '♣️': 'Trèfle'
        }
        return costume_map.get(emoji, 'Inconnu')


excel_predictor = ExcelPredictor()