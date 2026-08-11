from agent import find_query


result = find_query(
    "Hent Danmarks befolkning fra 2020 og frem",
    verbose=True,
)

print(result.query)
print()
print(result.code)