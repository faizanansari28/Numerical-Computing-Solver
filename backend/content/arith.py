from content.helpers import entry

CONTENT = {
"float_repr": entry(
    what="Floating-point representation is how computers store real numbers in binary using a sign, an exponent and a fraction (the IEEE 754 standard).",
    why="Computers have finite memory, so most real numbers can only be stored approximately. Knowing how explains strange results like 0.1 + 0.2 ≠ 0.3.",
    solves="Shows the exact bit pattern of a number, the value that is really stored, and the representation error.",
    uses="Understanding rounding errors in every numerical program, graphics, scientific computing, embedded systems.",
    explain="A double uses 64 bits: 1 sign bit, 11 exponent bits and 52 fraction bits. The number is stored in normalised scientific notation: (−1)ˢ × 2^(e − 1023) × (1.fraction)₂. The leading 1 is implied, so it gives a free extra bit of precision.",
    formula=r"x=(-1)^s\times 2^{\,e-1023}\times\Big(1+\sum_{i=1}^{52}b_i2^{-i}\Big)",
    variables=[[r"s", "sign bit"], [r"e", "11-bit exponent field (bias 1023)"], [r"b_i", "fraction bits"]],
    why_works="Any number that is not a sum of powers of 2 with at most 53 significant bits must be rounded to the nearest representable number. 0.1 = 0.0001100110011…₂ repeats forever in binary, so the stored value is 0.1000000000000000055511151231257827…",
    code='''
import struct

x = 0.1
raw = struct.unpack(">Q", struct.pack(">d", x))[0]      # the 64 bits of the double
bits = format(raw, "064b")

sign = bits[0]
exponent = bits[1:12]
fraction = bits[12:]

e = int(exponent, 2) - 1023                  # remove the bias
mantissa = 1 + int(fraction, 2) / 2**52      # 1.fraction
value = (-1) ** int(sign) * 2**e * mantissa

print("Sign bit =", sign)
print("Exponent =", exponent, "->", e)
print("Fraction =", fraction)
print("Value =", value)
''',
    adv=["Huge range of values (about 10⁻³⁰⁸ to 10³⁰⁸) in 64 bits.", "Constant relative precision (about 16 digits).", "Universal standard in hardware."],
    lim=["Most decimals cannot be stored exactly.", "Rounding errors accumulate.", "Overflow, underflow and loss of significance can occur."],
    related=["machine_eps", "rounding", "error_analysis"], example_intro="Look inside the double-precision number 0.1: its sign, exponent and fraction bits, and the tiny error in what is actually stored.",
),
"rounding": entry(
    what="Chopping (truncation) cuts a number off after k significant digits; rounding chooses the nearest k-digit number.",
    why="Every calculation on a computer or calculator ends by shortening numbers. These two rules decide how much error that causes.",
    solves="Shows the stored value and the error for chopping and rounding to 1-10 significant digits.",
    uses="Error analysis of numerical algorithms, calculators, financial rounding rules.",
    explain="Write the number in normalised form d.ddd… × 10ᵉ. Chopping simply drops every digit after the k-th. Rounding looks at the next digit: if it is 5 or more, increase the last kept digit by 1.",
    formula=r"|x-\mathrm{fl}_{\text{round}}(x)|\le\tfrac12\,10^{\,e-k+1},\qquad |x-\mathrm{fl}_{\text{chop}}(x)|<10^{\,e-k+1}",
    variables=[[r"k", "number of significant digits kept"], [r"e", "decimal exponent of x"], [r"\mathrm{fl}(x)", "the shortened (floating-point) version of x"]],
    why_works="The digits after position k contribute less than one unit in the k-th place, which bounds the chopping error. Rounding moves to whichever neighbour is nearer, so the error is at most half a unit - about twice as accurate.",
    code='''
import math

x = 3.14159265
k = 4                                        # significant digits to keep

exponent = math.floor(math.log10(abs(x)))    # x = d.ddd * 10^exponent
scale = 10 ** (k - 1 - exponent)

chopped = int(x * scale) / scale             # cut the digits off
rounded = math.floor(x * scale + 0.5) / scale   # nearest k-digit number

print("Chopped =", chopped, " error =", abs(x - chopped))
print("Rounded =", rounded, " error =", abs(x - rounded))
''',
    adv=["Rounding is unbiased and more accurate.", "Chopping is cheap in hardware."],
    lim=["Both introduce errors that can accumulate.", "Chopping always errs in the same direction (bias)."],
    related=["float_repr", "machine_eps", "error_analysis"], example_intro="Shorten π ≈ 3.14159265 to 4 significant digits by chopping (3.141) and rounding (3.142) and compare the errors.",
),
"machine_eps": entry(
    what="Machine epsilon is the gap between 1 and the next larger number the computer can represent: the smallest ε with 1 + ε > 1.",
    why="It measures the best relative accuracy any calculation can have. Anything smaller than ε relative to 1 simply vanishes.",
    solves="Computes ε by a simple halving loop and compares it with the theoretical value 2⁻⁵² (double) or 2⁻²³ (single).",
    uses="Choosing tolerances for iterative methods, understanding when two numbers are 'equal' on a computer.",
    explain="Start with ε = 1 and keep halving it while 1 + ε/2 is still bigger than 1. The last ε that still made a difference is the machine epsilon.",
    formula=r"\varepsilon=2^{-52}\approx2.22\times10^{-16}\ (\text{double}),\qquad \varepsilon=2^{-23}\approx1.19\times10^{-7}\ (\text{single})",
    variables=[[r"\varepsilon", "machine epsilon"], [r"p", "number of fraction bits (52 or 23)"], [r"\mathrm{fl}(x)=x(1+\delta)", "|δ| ≤ ε/2: relative error of each operation"]],
    why_works="Numbers just above 1 have the form 1 + k·2⁻⁵² (k = 1, 2, …) because the fraction has 52 bits, so the spacing there is 2⁻⁵². Anything smaller than half that spacing rounds back to 1. Hence the loop stops after exactly 52 halvings.",
    code='''
eps = 1.0

while 1.0 + eps / 2 > 1.0:                   # keep halving while 1 + eps/2 is still > 1
    eps = eps / 2

print("Machine epsilon =", eps)
print("0.1 + 0.2 =", 0.1 + 0.2)
print("0.1 + 0.2 == 0.3 ?", 0.1 + 0.2 == 0.3)
''',
    adv=["Gives a universal yardstick for accuracy.", "Easy to compute and verify."],
    lim=["Depends on the precision (single vs double).", "Absolute spacing grows with the size of the number."],
    related=["float_repr", "rounding", "error_analysis"], example_intro="Find the double-precision machine epsilon with the halving loop; it should equal 2⁻⁵² ≈ 2.22×10⁻¹⁶.", exact={"label": "Exact value 2⁻⁵²", "value": 2.0 ** -52},
),
"error_analysis": entry(
    what="Error analysis measures how far an approximation is from the true value and explains where the error comes from (truncation, rounding, …).",
    why="A numerical answer is useless unless we know how accurate it is. Error measures let us compare methods and decide when to stop.",
    solves="Computes absolute error, relative error, percentage error and the number of correct digits, or shows truncation error of a Taylor series.",
    uses="Every numerical method - convergence tests, tolerance settings, comparing algorithms.",
    explain="Absolute error |x − x̂| has the units of the quantity; relative error |x − x̂|/|x| is unit-free and shows how serious the error is (an error of 1 metre matters for a table, not for the distance to the Moon). Truncation error arises when an infinite process (like a series) is stopped early.",
    formula=r"E_{abs}=|x-\hat x|,\qquad E_{rel}=\frac{|x-\hat x|}{|x|},\qquad \Big|e^x-\sum_{k=0}^{n}\tfrac{x^k}{k!}\Big|\le\frac{\max(1,e^x)\,|x|^{n+1}}{(n+1)!}",
    variables=[[r"x", "exact (true) value"], [r"\hat x", "approximate value"], [r"n", "number of Taylor terms kept"]],
    why_works="Taylor's theorem says the remainder after n terms is f⁽ⁿ⁺¹⁾(ξ)xⁿ⁺¹/(n+1)! for some ξ between 0 and x; bounding f⁽ⁿ⁺¹⁾ = e^ξ gives the bound above, which shrinks rapidly because the factorial grows faster than any power.",
    code='''
exact = 3.14159265358979
approx = 3.14

abs_error = abs(exact - approx)              # how big is the mistake?
rel_error = abs_error / abs(exact)           # how big compared with the value?

print("Absolute error =", abs_error)
print("Relative error =", rel_error)
print("Percentage error =", rel_error * 100)
''',
    adv=["Quantifies the quality of any result.", "Relative error is comparable across problems.", "Error bounds let us choose parameters in advance."],
    lim=["Needs the exact value (or a bound) - in practice we estimate it.", "Relative error is undefined when the exact value is 0."],
    related=["machine_eps", "float_repr", "rounding"], example_intro="How good is 3.14 as an approximation of π? Compute the absolute, relative and percentage errors.",
),
}
