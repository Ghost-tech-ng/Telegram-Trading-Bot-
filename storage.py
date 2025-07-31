from typing import Dict, Any

# Shared storage for user data and crypto addresses
user_data: Dict[int, Dict[str, Any]] = {}

crypto_addresses: Dict[str, str] = {
    'Bitcoin': 'bc1qe4tluz39ac4zm3srnfnq5t9jpwrud256yw7g4j',
    'Ethereum': '0xAB8aDbEEb9E953db7687Fbb0E070aA9635E9D8D5',
    'USDT': '0xAB8aDbEEb9E953db7687Fbb0E070aA9635E9D8D5',
    'XRP': 'rpr5kJss1NMvtbzswshdxyW8ZEjmUCMt3e',
    'XLM': 'GCGGAXORHJASPJ25IKGKCW4WVWEUQ4US6JMYYDTTFVNUI54GEJ2Q6VAR',
    'BNB': '0xAB8aDbEEb9E953db7687Fbb0E070aA9635E9D8D5',
    'Solana': 'DaioFFCv6TBrZj8SDDGBYrDzGtE5Ei6QYJR2Exw1vmiX'
}