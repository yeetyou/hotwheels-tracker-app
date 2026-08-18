import requests
import json
import random
import time
from datetime import datetime
import os


# =========================
# CONFIG
# =========================

SHOP_URL = "https://prod-collectorshub.myshopify.com/api/2025-07/graphql.json"

TOKEN = "4e2b0149758b85fd897d97444fc09726"

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")

PRODUCT_FILE = "products.json"

BASE_PRODUCT_URL = "https://creations.mattel.com/products/"


HEADERS = {
    "X-Shopify-Storefront-Access-Token": TOKEN,
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0"
}



# =========================
# DISCORD
# =========================

def send_alert(message):

    if not DISCORD_WEBHOOK:
        print("Discord webhook missing")
        return


    try:

        # random human-like delay

        delay=random.uniform(1,3)

        print(f"Discord delay {delay:.2f}s")

        time.sleep(delay)


        r=requests.post(
            DISCORD_WEBHOOK,
            json={
                "content": message
            },
            timeout=10
        )


        print(
            "Discord:",
            r.status_code
        )


    except Exception as e:

        print(
            "Discord error:",
            e
        )



# =========================
# LOAD OLD DATA
# =========================

def load_old():

    try:

        with open(PRODUCT_FILE,"r") as f:

            return json.load(f)


    except:

        return {}



# =========================
# SAVE DATA
# =========================

def save(data):

    with open(PRODUCT_FILE,"w") as f:

        json.dump(
            data,
            f,
            indent=2
        )



# =========================
# SHOPIFY QUERY
# =========================

QUERY = """

query getProducts($cursor:String){

products(first:250,after:$cursor){

pageInfo{
hasNextPage
endCursor
}

edges{

node{

id
title
handle
availableForSale

variants(first:10){

edges{

node{

price{
amount
}

}

}

}

}

}

}

}

"""



# =========================
# GET PRODUCTS
# =========================

def get_products():

    products={}

    cursor=None


    while True:


        delay=random.uniform(1,4)

        print(
            f"Waiting {delay:.2f}s before request..."
        )

        time.sleep(delay)



        payload={

            "query":QUERY,

            "variables":{
                "cursor":cursor
            }

        }



        r=requests.post(
            SHOP_URL,
            headers=HEADERS,
            json=payload,
            timeout=20
        )


        print(
            "HTTP:",
            r.status_code
        )



        try:

            data=r.json()


        except:

            print(
                r.text[:500]
            )

            break



        if r.status_code != 200:

            print(
                "HTTP ERROR:",
                data
            )

            break



        if "errors" in data:

            print(
                "GRAPHQL ERROR:",
                data["errors"]
            )

            break



        for edge in data["data"]["products"]["edges"]:


            p=edge["node"]

            title=p["title"]



            # Only Hot Wheels

            if "hot wheels" not in title.lower():

                continue



            price=None


            try:

                price=float(
                    p["variants"]
                    ["edges"][0]
                    ["node"]
                    ["price"]
                    ["amount"]
                )

            except:

                pass



            products[p["id"]] = {

                "title": title,

                "handle": p["handle"],

                "available": p["availableForSale"],

                "price": price

            }



        page=data["data"]["products"]["pageInfo"]


        if not page["hasNextPage"]:

            break


        cursor=page["endCursor"]



    return products





# =========================
# CHECK CHANGES
# =========================

def check():

    print(
        "\nChecking Mattel:",
        datetime.now()
    )


    old=load_old()


    new=get_products()


    print(
        "Products found:",
        len(new)
    )



    alerts=[]



    for pid,item in new.items():


        link = BASE_PRODUCT_URL + item["handle"]



        # NEW PRODUCT

        if pid not in old:


            alerts.append(

                "🆕 NEW PRODUCT\n"
                f"{item['title']}\n"
                f"{link}"

            )


            continue





        old_item=old[pid]



        # RESTOCK

        if (
            not old_item.get("available")
            and item["available"]
        ):


            alerts.append(

                "🔥 RESTOCK\n"
                f"{item['title']}\n"
                f"{link}"

            )





        # PRICE CHANGE

        if (
            old_item.get("price")
            !=
            item.get("price")
        ):


            alerts.append(

                "💰 PRICE CHANGE\n"
                f"{item['title']}\n"
                f"${old_item.get('price')} → ${item.get('price')}\n"
                f"{link}"

            )





    if alerts:


        for alert in alerts:

            print("\n",alert)

            send_alert(alert)



    else:

        print(
            "No changes detected"
        )



    save(new)





if __name__=="__main__":

    check()
