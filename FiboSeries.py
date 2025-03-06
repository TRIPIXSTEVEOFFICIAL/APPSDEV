print("\nVincent C. Dumaguet")
print("Activity #4")
print("Date: 3/4/2025")

n = int(input("Enter the number of terms: "))

a, b = 0,1

print("Fibonacci Series: ")

for _ in range(n):
    print(a, end=" ")
    a, b = b, a + b