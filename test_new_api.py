from src.infrastructure.recommender_impl import MLRecommender

rec = MLRecommender()
result = rec.recommend('Adi', 'happy', 3)
print(f'Got {len(result)} recommendations:')
for r in result:
    print(f'  - {r["title"]} ({r["year"]}) - {r["reason"][:50]}')
