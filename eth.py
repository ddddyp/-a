import requests

# 使用Etherscan API服务
api_key = 'your-api-key'
base_url = 'https://yunwu.ai/v1'


def get_eth_balance(address):
    """
    查询以太坊账户余额

    :param address: 以太坊地址
    :return: 账户余额（单位：Wei）
    """
    url = f'{base_url}/api?module=account&action=balance&address={address}&tag=latest&apikey={api_key}'
    response = requests.get(url)
    data = response.json()

    if data['status'] == '1':
        return int(data['result'])
    else:
        raise Exception(data['message'])


# 示例以太坊地址
address = '0xde0b295669a9fd93d5f28d9ec85e40f4cb697bae'
balance = get_eth_balance(address)
print(f'Address: {address}')
print(f'Balance: {balance} Wei')
