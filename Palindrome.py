print("\nVincent C. Dumaguet")
print("Activity #5")
print("Date: 3/4/2025")

num = input("Enter a number: ")

if num == num[::-1]:
    print(f"{num} is a palindrome. ")
else:
    print(f"{num} is not a palindrome.")