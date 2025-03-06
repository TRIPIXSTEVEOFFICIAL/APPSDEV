print("\nVincent C. Dumaguet")
print("Activity #2")
print("Date: 3/4/2025")

num = int(input("Enter a number: "))
num_str = str(num)
num_length = len(num_str)
sum_of_digits = sum(int(digit) ** num_length for digit in num_str)

if num == sum_of_digits:
    print(f"{num} is an Armstrong number.")
else:
    print(f"{num} is not an Armstrong number.")