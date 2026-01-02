from typing import Dict, Any

# Shared storage for user data and crypto addresses
user_data: Dict[int, Dict[str, Any]] = {}

crypto_addresses: Dict[str, str] = {
    'Bitcoin': 'bc1qvy8t9tn96c55vq0mk2tzgkcaews23a0jldqlzr',
    'Ethereum': '0x251601f4c7f9708a5a2E1A1A0ead87886D28FD6A',
    'USDT(ERC20)': '0x251601f4c7f9708a5a2E1A1A0ead87886D28FD6A',
    'XRP': 'rUfe1havVukiCcvvUupD5kCBkgMABjP1xk',
    'XLM': 'GANOQPCXRJO6DOGT6BFPKMKG2EFP33EATNRSJUH3ZWDCZVISSXAMIF4F',
    'BNB': '0x251601f4c7f9708a5a2E1A1A0ead87886D28FD6A',
    'Solana': 'FivNN2VAtrsaNAoj6gYbKmZnebYy54R3uQmTM7mh72xF'
}