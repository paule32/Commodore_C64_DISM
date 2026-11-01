import pyodbc

print("pyodbc:", pyodbc.version)

for driver in pyodbc.drivers():
    print(driver)
