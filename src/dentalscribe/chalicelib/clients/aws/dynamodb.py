from typing import Dict, Any, Optional, List
from chalicelib.clients.aws.base import BaseAWSClient

class DynamoDBClient(BaseAWSClient):
    def __init__(self, region: Optional[str] = None):
        super().__init__('dynamodb', region)
        self.BATCH_SIZE = 25

    def get_item(self, table_name, key: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        response = self.client.get_item(
            TableName=table_name,
            Key=key
        )

        return response.get("Item", None)
    
    def query_items(self, table_name, index_name: Optional[str], key_condition_expression: str, expression_attribute_values: Dict[str, Any]) -> List[Dict[str, Any]]:
        if index_name:
            response = self.client.query(
                TableName=table_name,
                IndexName=index_name,
                KeyConditionExpression=key_condition_expression,
                ExpressionAttributeValues=expression_attribute_values
            )
        else:
            response = self.client.query(
                TableName=table_name,
                KeyConditionExpression=key_condition_expression,
                ExpressionAttributeValues=expression_attribute_values
            )
        return response.get("Items", [])
    
    def filter_items(self, table_name, index_name: Optional[str], key: Dict[str, Any]) -> List[Dict[str, Any]]:
        condition_expression = " AND ".join([f"{k} = :{k}" for k in key.keys()])
        expression_attribute_values = {f":{k}": v for k, v in key.items()}
        return self.query_items(table_name, index_name, condition_expression, expression_attribute_values)



    def put_item(self, table_name, item: Dict[str, Any]) -> Dict[str, Any]:
        response = self.client.put_item(
            TableName=table_name,
            Item=item
        )
        return response
    
    def update_item(self, table_name, key: Dict[str, Any], update_expression: str, expression_attribute_values: Dict[str, Any]) -> Dict[str, Any]:
        response = self.client.update_item(
            TableName=table_name,
            Key=key,
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values
        )
        return response
    
    def delete_item(self, table_name, key: Dict[str, Any]) -> Dict[str, Any]:
        response = self.client.delete_item(
            TableName=table_name,
            Key=key
        )
        return response


    def bulk_update(self, table_name: str, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        複数のアイテムを一括更新する
        
        Args:
            table_name: テーブル名
            items: 更新するアイテムのリスト

        Returns:
            失敗したアイテムのリスト
        """
        failed_items = []

        # バッチサイズごとに処理
        for batch in self._chunk_list(items, self.BATCH_SIZE):
            request_items = {
                table_name: [
                    {
                        'PutRequest': {
                            'Item': item
                        }
                    } for item in batch
                ]
            }

            try:
                response = self.client.batch_write_item(
                    RequestItems=request_items,
                    ReturnConsumedCapacity='NONE'
                )

                # 未処理のアイテムを再試行
                unprocessed_items = response.get('UnprocessedItems', {}).get(table_name, [])
                if unprocessed_items:
                    failed_items.extend([
                        item['PutRequest']['Item'] 
                        for item in unprocessed_items
                    ])

            except Exception as e:
                failed_items.extend(batch)

        return failed_items

    def bulk_delete(self, table_name: str, keys: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        複数のアイテムを一括削除する
        
        Args:
            table_name: テーブル名
            keys: 削除するアイテムのキーのリスト

        Returns:
            失敗したキーのリスト
        """
        failed_keys = []

        # バッチサイズごとに処理
        for batch in self._chunk_list(keys, self.BATCH_SIZE):
            request_items = {
                table_name: [
                    {
                        'DeleteRequest': {
                            'Key': key
                        }
                    } for key in batch
                ]
            }

            try:
                response = self.client.batch_write_item(
                    RequestItems=request_items,
                    ReturnConsumedCapacity='NONE'
                )

                # 未処理のアイテムを再試行
                unprocessed_items = response.get('UnprocessedItems', {}).get(table_name, [])
                if unprocessed_items:
                    failed_keys.extend([
                        item['DeleteRequest']['Key'] 
                        for item in unprocessed_items
                    ])

            except Exception as e:
                failed_keys.extend(batch)

        return failed_keys

    def _chunk_list(self, items: List[Any], chunk_size: int) -> List[List[Any]]:
        """リストをチャンクサイズごとに分割する"""
        return [
            items[i:i + chunk_size] 
            for i in range(0, len(items), chunk_size)
        ]