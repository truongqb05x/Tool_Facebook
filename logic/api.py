import requests
from urllib.parse import urlparse, parse_qs
from collections import defaultdict

GRAPH_VERSION = "v23.0"

ACCESS_TOKEN = "EAAAAUaZA8jlABQZCL1oJNvgQZCqmbXsmlFdYO1C8VmhZAJnoCqfS1rsaac4iyQwu1jIDrw1SSYvcxZBuzt49vwxqlmH9PsCUyZBdmeYZCCNqw5Ku6Wc1y0W1d9EBxvGiImxGateWPE2vQpag5XbYZClxxLLRt9D6e5jOL8K9UosIZArWtHAxZAkgoiRM4ZBmw3aJ8tRCdcLmwZDZD"

REACTION_NAMES = {
    "LIKE": "👍 LIKE",
    "LOVE": "❤️ LOVE",
    "HAHA": "😂 HAHA",
    "WOW": "😮 WOW",
    "SAD": "😢 SAD",
    "ANGRY": "😡 ANGRY",
    "CARE": "🤗 CARE",
}


def get_fbid_from_url(facebook_url):
    """Lấy fbid từ URL Facebook."""

    try:
        parsed = urlparse(facebook_url)
        params = parse_qs(parsed.query)

        fbid = params.get("fbid")

        if fbid:
            return fbid[0]

    except Exception:
        pass

    return None


def get_all_reactions(fbid):
    """Lấy toàn bộ reactions qua pagination."""

    url = f"https://graph.facebook.com/{GRAPH_VERSION}/{fbid}/reactions"

    params = {
        "access_token": ACCESS_TOKEN,
        "fields": "id,name,type",
        "limit": 100
    }

    all_reactions = []

    while url:

        try:
            response = requests.get(
                url,
                params=params,
                timeout=30
            )

        except requests.RequestException as e:
            print(f"❌ Request error: {e}")
            break

        try:
            data = response.json()
        except Exception:
            print(response.text)
            break

        if response.status_code != 200:
            print("\n❌ Graph API Error")
            print(data)
            break

        reactions = data.get("data", [])

        all_reactions.extend(reactions)

        # Các request tiếp theo đã có access_token trong URL
        # nên không cần truyền params nữa
        paging = data.get("paging", {})
        url = paging.get("next")

        params = None

    return all_reactions


def print_reactions(reactions):
    """Phân loại và in reactions."""

    grouped = defaultdict(list)

    for user in reactions:

        reaction_type = user.get("type", "UNKNOWN")

        grouped[reaction_type].append({
            "id": user.get("id"),
            "name": user.get("name")
        })

    # Thứ tự muốn hiển thị
    reaction_order = [
        "LIKE",
        "LOVE",
        "HAHA",
        "WOW",
        "SAD",
        "ANGRY",
        "CARE"
    ]

    print("\n" + "=" * 60)
    print("           FACEBOOK REACTIONS")
    print("=" * 60)

    print(f"\nTổng reaction: {len(reactions)}")

    total_users = 0

    for reaction_type in reaction_order:

        users = grouped.get(reaction_type, [])

        if not users:
            continue

        reaction_name = REACTION_NAMES.get(
            reaction_type,
            reaction_type
        )

        print("\n" + "-" * 60)
        print(f"{reaction_name} — {len(users)} người")
        print("-" * 60)

        for index, user in enumerate(users, 1):

            print(
                f"{index:>3}. "
                f"UID: {user['id']} | "
                f"Name: {user['name']}"
            )

        total_users += len(users)

    # Các reaction lạ nếu API trả về
    unknown_types = [
        key for key in grouped
        if key not in reaction_order
    ]

    for reaction_type in unknown_types:

        users = grouped[reaction_type]

        print("\n" + "-" * 60)
        print(f"❓ {reaction_type} — {len(users)} người")
        print("-" * 60)

        for index, user in enumerate(users, 1):

            print(
                f"{index:>3}. "
                f"UID: {user['id']} | "
                f"Name: {user['name']}"
            )

        total_users += len(users)

    print("\n" + "=" * 60)
    print("THỐNG KÊ")
    print("=" * 60)

    for reaction_type in reaction_order:

        count = len(grouped.get(reaction_type, []))

        if count:
            print(
                f"{REACTION_NAMES.get(reaction_type, reaction_type)}:"
                f" {count}"
            )

    print("-" * 60)
    print(f"TỔNG: {total_users}")
    print("=" * 60)


def main():

    if ACCESS_TOKEN == "YOUR_ACCESS_TOKEN":
        print("❌ Hãy nhập ACCESS_TOKEN.")
        return

    facebook_url = input(
        "Nhập link Facebook: "
    ).strip()

    fbid = get_fbid_from_url(facebook_url)

    if not fbid:
        print(
            "❌ Không tìm thấy fbid trong URL."
        )
        return

    print(f"\nFBID: {fbid}")
    print("Đang lấy reactions...")

    reactions = get_all_reactions(fbid)

    if not reactions:
        print("\n⚠️ Không lấy được reaction nào.")
        return

    print_reactions(reactions)


if __name__ == "__main__":
    main()