import socket

# 各エージェントごとのパラメータ設定（例）
agent_params = {
    1: {"omega": 3.14 * 6.2, "kappa": 1.0, "alpha": 0.5},
    2: {"omega": 3.14 * 6.0, "kappa": 1.0, "alpha": 0.6},
    3: {"omega": 3.14 * 6.0, "kappa": 1.0, "alpha": 0.7},
    4: {"omega": 3.14 * 5.9, "kappa": 1.0, "alpha": 0.8},
    # 必要に応じて他のエージェントの設定を追加
}

def udp_param_server_thread(port=5001):
    """
    指定ポートでUDPによるパラメータ要求を待ち受け、
    エージェントのリクエストに応じて "PARAM,omega=...,kappa=...,alpha=..." のような文字列を返す。
    
    リクエスト例: "REQUEST_PARAM,agent=2"
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", port))
    print(f"[INFO] Parameter server listening on port {port}")

    while True:
        data, addr = sock.recvfrom(1024)
        req = data.decode(errors='ignore').strip()
        if req.startswith("REQUEST_PARAM"):
            try:
                # リクエスト文字列をカンマで分割し、"agent=" が含まれる部分からエージェント番号を取得
                parts = req.split(',')
                agent_id = None
                for part in parts:
                    if part.startswith("agent="):
                        agent_id = int(part.split('=')[1])
                        break
                if agent_id is None:
                    raise ValueError("agent id not found")
            except Exception as e:
                response = f"ERROR, invalid request: {e}"
                sock.sendto(response.encode(), addr)
                continue
            
            # エージェント番号に対応するパラメータを取得
            params = agent_params.get(agent_id)
            if params is None:
                response = f"ERROR, unknown agent id {agent_id}"
            else:
                response = (f"PARAM,omega={params['omega']},"
                            f"kappa={params['kappa']},"
                            f"alpha={params['alpha']}")
            
            sock.sendto(response.encode(), addr)
