from chalicelib.prompts.schemas.base import BaseSchema

class Voice2SoapSchema(BaseSchema):
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["subjective", "objective", "assessment", "plan"],
        "properties": {
            "subjective": {
                "type": "string",
                "description": "患者の主訴、症状の経過、既往歴、服薬状況、アレルギー歴など主観的情報"
            },
            "objective": {
                "type": "string",
                "description": "口腔内所見、X線所見、歯周組織検査結果、バイタルサイン、口腔外所見など客観的情報"
            },
            "assessment": {
                "type": "string",
                "description": "歯科診断、重症度評価、リスク要因、予後予測など"
            },
            "plan": {
                "type": "string",
                "description": "治療方針・順序、処方、口腔衛生指導、次回予約・フォローアップ計画、専門医紹介の必要性など"
            }
        }
    }

    def validate(self, data):
        """データがスキーマに適合するかを検証"""
        required_fields = ["subjective", "objective", "assessment", "plan"]
        
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")
            
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Required field '{field}' is missing")
            if not isinstance(data[field], str):
                raise ValueError(f"Field '{field}' must be a string")