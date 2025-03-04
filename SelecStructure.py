print("\nVincent C. Dumaguet")
print("Activity #1")
print("Date 3/4/2025")

def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
        return True
lower = int(input("Enter the lower bound: "))
upper = int(input("Enter the upper bound: "))

print(f"Prime numbers between {lower} and {upper} are: ")

for num in range(lower, upper + 1):
    if is_prime(num):
        print(num , end =",")