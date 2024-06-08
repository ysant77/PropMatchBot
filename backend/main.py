from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .database import create_tables, get_db_connection
from .models import TenantProfile, SubscriptionRequest, PaymentRequest, PropertySuggestionRequest, UserProfile
from .utils import embed_text
import numpy as np
import sqlite3
import os
import stripe

# Initialize FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Stripe
stripe.api_key = os.environ['STRIPE_API_KEY']

# Create tables on startup
create_tables()

@app.post("/tenant_profile")
def create_update_tenant_profile(profile: TenantProfile):
    conn = get_db_connection()
    cursor = conn.cursor()
    embedding = embed_text(f"{profile.gender} {profile.age} {profile.nationality} {profile.race} {profile.occupation} {profile.work_pass} {profile.moving_in_date} {profile.length_of_stay} {profile.budget}")

    cursor.execute('SELECT * FROM tenant_profiles WHERE user_id = ?', (profile.user_id,))
    if cursor.fetchone():
        cursor.execute('''
            UPDATE tenant_profiles
            SET gender = ?, age = ?, nationality = ?, race = ?, occupation = ?, work_pass = ?, moving_in_date = ?, length_of_stay = ?, budget = ?, embedding = ?
            WHERE user_id = ?
        ''', (profile.gender, profile.age, profile.nationality, profile.race, profile.occupation, profile.work_pass, profile.moving_in_date, profile.length_of_stay, profile.budget, sqlite3.Binary(np.array(embedding).tobytes()), profile.user_id))
    else:
        cursor.execute('''
            INSERT INTO tenant_profiles (user_id, gender, age, nationality, race, occupation, work_pass, moving_in_date, length_of_stay, budget, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (profile.user_id, profile.gender, profile.age, profile.nationality, profile.race, profile.occupation, profile.work_pass, profile.moving_in_date, profile.length_of_stay, profile.budget, sqlite3.Binary(np.array(embedding).tobytes())))
    conn.commit()

    cursor.close()
    conn.close()
    return {"message": "Tenant profile updated successfully"}

@app.post("/ingest_tenants")
def ingest_tenants():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tenant')
    tenants = cursor.fetchall()
    for tenant in tenants:
        tenant_text = f"{tenant['gender']} {tenant['age']} {tenant['nationality']} {tenant['race']} {tenant['occupation']} {tenant['work_pass']} {tenant['moving_in_date']} {tenant['length_of_stay']} {tenant['budget']}"
        embedding = embed_text(tenant_text)
        cursor.execute('UPDATE tenant SET embedding = ? WHERE tenant_id = ?', (sqlite3.Binary(np.array(embedding).tobytes()), tenant['tenant_id']))
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "Tenants ingested and embeddings updated successfully"}

@app.get("/subscription/{user_id}")
def get_subscription(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT subscription FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    if result:
        return {"user_id": user_id, "subscription": result["subscription"]}
    else:
        return {"user_id": user_id, "subscription": "basic"}

@app.post("/subscription")
def update_subscription(request: SubscriptionRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (request.user_id,))
    if cursor.fetchone():
        cursor.execute('UPDATE users SET subscription = ? WHERE user_id = ?', (request.subscription, request.user_id))
    else:
        cursor.execute('INSERT INTO users (user_id, subscription) VALUES (?, ?)', (request.user_id, request.subscription))
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "Subscription updated successfully"}

@app.post("/profile")
def create_update_profile(profile: UserProfile):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (profile.user_id,))
    if cursor.fetchone():
        cursor.execute('UPDATE users SET name = ?, subscription = ? WHERE user_id = ?', (profile.name, profile.subscription, profile.user_id))
    else:
        cursor.execute('INSERT INTO users (user_id, name, subscription) VALUES (?, ?, ?)', (profile.user_id, profile.name, profile.subscription))
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "Profile updated successfully"}

@app.post("/property_suggestions")
def property_suggestions(request: PropertySuggestionRequest):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM tenant_profiles WHERE user_id = ?', (request.user_id,))
    tenant_profile = cursor.fetchone()
    if not tenant_profile:
        raise HTTPException(status_code=404, detail="Tenant profile not found")

    query_embedding = np.frombuffer(tenant_profile['embedding'], dtype=np.float32)
    cursor.execute('SELECT * FROM tenant')
    tenants = cursor.fetchall()

    tenant_vectors = []
    for tenant in tenants:
        tenant_vectors.append((tenant['tenant_id'], np.frombuffer(tenant['embedding'], dtype=np.float32)))

    tenant_vectors = np.array([vector for _, vector in tenant_vectors])
    similarity_scores = np.dot(tenant_vectors, query_embedding) / (np.linalg.norm(tenant_vectors, axis=1) * np.linalg.norm(query_embedding))
    top_matches = sorted(zip(tenants, similarity_scores), key=lambda x: x[1], reverse=True)[:20]

    tenant_ids = [match[0]['tenant_id'] for match in top_matches]

    cursor.execute(f'''
        SELECT Property.* FROM Property
        JOIN mapping ON Property.id = mapping.id
        WHERE mapping.tenant_id IN ({",".join(["?"]*len(tenant_ids))})
    ''', tenant_ids)
    properties = cursor.fetchall()
    cursor.close()
    conn.close()

    if request.subscription == "basic":
        max_results = 5
    elif request.subscription == "standard":
        max_results = 10
    else:
        max_results = 20

    suggested_properties = [{"property_id": prop['id'], "PropertyName": prop['property_name'], "Type": prop['type'], "Price": prop['price'], "Bedrooms": prop['bedrooms'], "Bathrooms": prop['bathrooms'], "Sqft": prop['sqft'], "Author": prop['author'], "MoveInDate": prop['move_in_date']} for prop in properties[:max_results]]
    unique_suggested_properties = list({tuple(d.items()) for d in suggested_properties})
    suggested_properties = [dict(t) for t in unique_suggested_properties]

    return {"suggested_properties": suggested_properties}

@app.get("/tenant_profile/{user_id}")
def get_tenant_profile(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tenant_profiles WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    if result:
        return dict(result)
    else:
        return {"message": "Tenant profile not found"}

@app.get("/profile/{user_id}")
def get_profile(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    if result:
        return {"user_id": user_id, "name": result["name"], "subscription": result["subscription"]}
    else:
        return {"user_id": user_id, "name": "", "subscription": "basic"}

@app.post("/create-payment-intent")
def create_payment_intent(request: PaymentRequest):
    amount = 10000 if request.subscription == "standard" else 20000
    try:
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency='usd',
            automatic_payment_methods={"enabled": True, "allow_redirects": "never"}
        )
        update_subscription(SubscriptionRequest(user_id=request.user_id, subscription=request.subscription))
        return {"client_secret": intent.client_secret}
    except stripe.error.CardError as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
