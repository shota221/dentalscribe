
from datetime import datetime, timezone, timedelta
from typing import Union, Optional
from enum import Enum
from zoneinfo import ZoneInfo

class TimeFormat(Enum):
    """時刻のフォーマット定義"""
    BASIC = "%Y-%m-%d %H:%M:%S"
    ISO = "%Y-%m-%dT%H:%M:%S%z"
    DATE = "%Y-%m-%d"
    TIME = "%H:%M:%S"
    COMPACT = "%Y%m%d%H%M%S"
    MONTH = "%Y-%m"

class TimeUtil:
    """時刻操作ユーティリティクラス"""
    
    JST = ZoneInfo("Asia/Tokyo")
    UTC = timezone.utc
    
    @staticmethod
    def to_jst(dt: Union[str, datetime, float], 
               input_format: Optional[str] = None) -> datetime:
        """
        UTCの時刻をJSTに変換する

        Args:
            dt: 変換対象の時刻（文字列、datetime、タイムスタンプのいずれか）
            input_format: 入力が文字列の場合のフォーマット

        Returns:
            datetime: JST timezone付きのdatetime
        """
        if isinstance(dt, str):
            dt = datetime.strptime(dt, input_format or TimeFormat.BASIC.value)
        elif isinstance(dt, float):
            dt = datetime.fromtimestamp(dt)
            
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=TimeUtil.UTC)
            
        return dt.astimezone(TimeUtil.JST)

    @staticmethod
    def format_jst(dt: Union[str, datetime, float], 
                   output_format: TimeFormat = TimeFormat.BASIC,
                   input_format: Optional[str] = None) -> str:
        """
        時刻をJSTの文字列に変換する

        Args:
            dt: 変換対象の時刻
            output_format: 出力フォーマット
            input_format: 入力が文字列の場合のフォーマット

        Returns:
            str: フォーマットされた時刻文字列
        """
        jst_dt = TimeUtil.to_jst(dt, input_format)
        return jst_dt.strftime(output_format.value)

    @staticmethod
    def now(tz: timezone = JST) -> datetime:
        """
        指定したタイムゾーンの現在時刻を取得する

        Args:
            tz: タイムゾーン（デフォルト: JST）

        Returns:
            datetime: タイムゾーン付きの現在時刻
        """
        return datetime.now(tz)

    @staticmethod
    def now_str(fmt: TimeFormat = TimeFormat.BASIC, tz: timezone = JST) -> str:
        """
        指定したタイムゾーンの現在時刻を文字列で取得する

        Args:
            fmt: 出力フォーマット
            tz: タイムゾーン（デフォルト: JST）

        Returns:
            str: フォーマットされた現在時刻
        """
        return TimeUtil.now(tz).strftime(fmt.value)

    @staticmethod
    def timestamp() -> float:
        """
        現在のUNIXタイムスタンプを取得する

        Returns:
            float: UNIXタイムスタンプ
        """
        return datetime.now(TimeUtil.UTC).timestamp()

    @staticmethod
    def diff_seconds(dt1: Union[str, datetime], 
                    dt2: Union[str, datetime],
                    fmt: Optional[str] = None) -> float:
        """
        2つの時刻の差分を秒数で取得する

        Args:
            dt1: 比較する時刻1
            dt2: 比較する時刻2
            fmt: 入力が文字列の場合のフォーマット

        Returns:
            float: 差分（秒）
        """
        if isinstance(dt1, str):
            dt1 = datetime.strptime(dt1, fmt or TimeFormat.BASIC.value)
        if isinstance(dt2, str):
            dt2 = datetime.strptime(dt2, fmt or TimeFormat.BASIC.value)
        
        return (dt1 - dt2).total_seconds()

    @staticmethod
    def add_days(dt: Union[str, datetime], 
                 days: int,
                 fmt: Optional[str] = None) -> datetime:
        """
        指定した日数を加算・減算する

        Args:
            dt: 基準時刻
            days: 加算する日数（負数の場合は減算）
            fmt: 入力が文字列の場合のフォーマット

        Returns:
            datetime: 計算後の時刻
        """
        if isinstance(dt, str):
            dt = datetime.strptime(dt, fmt or TimeFormat.BASIC.value)
        
        return dt + timedelta(days=days)

    @staticmethod
    def yesterday(tz: timezone = JST) -> datetime:
        """
        指定したタイムゾーンの昨日の日付を取得する

        Args:
            tz: タイムゾーン（デフォルト: JST）

        Returns:
            datetime: 昨日の日付
        """
        return TimeUtil.now(tz) - timedelta(days=1)
    
    @staticmethod
    def yesterday_str(fmt: TimeFormat = TimeFormat.DATE, tz: timezone = JST) -> str:
        """
        指定したタイムゾーンの昨日の日付を文字列で取得する

        Args:
            fmt: 出力フォーマット
            tz: タイムゾーン（デフォルト: JST）

        Returns:
            str: フォーマットされた昨日の日付
        """
        return TimeUtil.yesterday(tz).strftime(fmt.value)

    @staticmethod
    def is_same_day(dt1: Union[str, datetime], 
                    dt2: Union[str, datetime],
                    fmt: Optional[str] = None) -> bool:
        """
        2つの時刻が同じ日かどうかを判定する

        Args:
            dt1: 比較する時刻1
            dt2: 比較する時刻2
            fmt: 入力が文字列の場合のフォーマット

        Returns:
            bool: 同じ日の場合はTrue
        """
        if isinstance(dt1, str):
            dt1 = datetime.strptime(dt1, fmt or TimeFormat.BASIC.value)
        if isinstance(dt2, str):
            dt2 = datetime.strptime(dt2, fmt or TimeFormat.BASIC.value)
        
        return dt1.date() == dt2.date()
    
    @staticmethod
    def get_date(dt: Union[str, datetime], 
                 fmt: Optional[str] = None) -> str:
        """
        時刻から日付部分を取得する

        Args:
            dt: 時刻
            fmt: 入力が文字列の場合のフォーマット

        Returns:
            str: 日付文字列
        """
        if isinstance(dt, str):
            dt = datetime.strptime(dt, fmt or TimeFormat.BASIC.value)
        
        return dt.strftime(TimeFormat.DATE.value)