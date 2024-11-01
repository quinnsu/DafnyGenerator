method IsProductEven(arr: array<int>) returns (isEven: bool)
    requires arr != null
    ensures isEven == (ProductIsEven(arr))
{
    var product := 1;
    var i := 0;

    while i < arr.Length
        invariant 0 <= i <= arr.Length
        invariant product == Product(arr, 0, i)
    {
        product := product * arr[i];
        i := i + 1;
    }

    isEven := (product % 2 == 0);
}

method Product(arr: array<int>, start: int, end: int) returns (prod: int)
    requires 0 <= start <= end <= arr.Length
    ensures prod == (if end == start then 1 else arr[start] * Product(arr, start + 1, end))
{
    if start == end {
        return 1;
    }
    return arr[start] * Product(arr, start + 1, end);
}

method ProductIsEven(arr: array<int>) returns (isEven: bool)
    requires arr != null
    ensures isEven == (exists i :: 0 <= i < arr.Length && arr[i] % 2 == 0)
{
    var i := 0;
    while i < arr.Length
        invariant 0 <= i <= arr.Length
    {
        if arr[i] % 2 == 0 {
            return true;
        }
        i := i + 1;
    }
    return false;
}