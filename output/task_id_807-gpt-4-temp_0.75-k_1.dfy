method FindFirstOdd(arr: array<int>) returns (result: int)
    requires arr != null
    ensures result == -1 || result % 2 == 1 // Result is -1 if no odd number is found, or an odd number
{
    var i := 0;
    while i < arr.Length
        invariant 0 <= i <= arr.Length
        invariant forall j: int :: 0 <= j < i ==> arr[j] % 2 == 0
    {
        if arr[i] % 2 == 1 {
            return arr[i]; // Return the first odd number
        }
        i := i + 1; // Move to the next element
    }
    return -1; // Return -1 if no odd number is found
}