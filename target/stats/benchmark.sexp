(benchmark
  :"jpamb.cases.Arrays.arrayContent!()V" (control
    :coverage (
      :"jpamb.cases.Arrays.arrayContent:()V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 39 40 41)
      )
    )
    :results ("assertion error")
  )
  :"jpamb.cases.Arrays.arrayContentAboveMinus13!()V" (control
    :coverage (
      :"jpamb.cases.Arrays.arrayContentAboveMinus13:()V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 40 41 42)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Arrays.arrayInBounds!()V" (control
    :coverage (
      :"jpamb.cases.Arrays.arrayInBounds:()V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Arrays.arrayIndexValue!(4)V" (control
    :coverage (
      :"jpamb.cases.Arrays.arrayIndexValue:(I)V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 52)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Arrays.arrayIndexValue!(5)V" (control
    :coverage (
      :"jpamb.cases.Arrays.arrayIndexValue:(I)V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48)
      )
    )
    :results ("assertion error")
  )
  :"jpamb.cases.Arrays.arrayIsNull!()V" (control
    :coverage (
      :"jpamb.cases.Arrays.arrayIsNull:()V" (coverage
        :reachable (0 1 2 3 4 5)
      )
    )
    :results ("null pointer")
  )
  :"jpamb.cases.Arrays.arrayIsNullLength!()V" (control
    :coverage (
      :"jpamb.cases.Arrays.arrayIsNullLength:()V" (coverage
        :reachable (0 1 2 3 4 5)
      )
    )
    :results ("null pointer")
  )
  :"jpamb.cases.Arrays.arrayLength!()V" (control
    :coverage (
      :"jpamb.cases.Arrays.arrayLength:()V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 21)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Arrays.arrayLoop!(5)V" (control
    :coverage (
      :"jpamb.cases.Arrays.arrayLoop:(I)V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Arrays.arrayLoop!(6)V" (control
    :coverage (
      :"jpamb.cases.Arrays.arrayLoop:(I)V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16)
      )
    )
    :results ("assertion error")
  )
  :"jpamb.cases.Arrays.arrayNotEmpty!([I:1])V" (control
    :coverage (
      :"jpamb.cases.Arrays.arrayNotEmpty:([I)V" (coverage
        :reachable (0 1 2 3 4 9)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Arrays.arrayNotEmpty!([I:])V" (control
    :coverage (
      :"jpamb.cases.Arrays.arrayNotEmpty:([I)V" (coverage
        :reachable (0 1 2 3 4 5)
      )
    )
    :results ("assertion error")
  )
  :"jpamb.cases.Arrays.arrayOutOfBounds!()V" (control
    :coverage (
      :"jpamb.cases.Arrays.arrayOutOfBounds:()V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 13 14)
      )
    )
    :results ("out of bounds")
  )
  :"jpamb.cases.Arrays.arraySometimesNull!(0)V" (control
    :coverage (
      :"jpamb.cases.Arrays.arraySometimesNull:(I)V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15)
      )
    )
    :results ("out of bounds")
  )
  :"jpamb.cases.Arrays.arraySometimesNull!(11)V" (control
    :coverage (
      :"jpamb.cases.Arrays.arraySometimesNull:(I)V" (coverage
        :reachable (0 1 2 3 4 12 13 14 15)
      )
    )
    :results ("null pointer")
  )
  :"jpamb.cases.Arrays.arraySpellsHello!([C:'h', 'e', 'l', 'l', 'o'])V" (control
    :coverage (
      :"jpamb.cases.Arrays.arraySpellsHello:([C)V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 31)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Arrays.arraySpellsHello!([C:'x'])V" (control
    :coverage (
      :"jpamb.cases.Arrays.arraySpellsHello:([C)V" (coverage
        :reachable (0 1 2 3 4 5 6 27)
      )
    )
    :results ("assertion error")
  )
  :"jpamb.cases.Arrays.arraySpellsHello!([C:])V" (control
    :coverage (
      :"jpamb.cases.Arrays.arraySpellsHello:([C)V" (coverage
        :reachable (0 1 2 3 4)
      )
    )
    :results ("out of bounds")
  )
  :"jpamb.cases.Arrays.arraySumIsLarge!([I:50, 100, 200])V" (control
    :coverage (
      :"jpamb.cases.Arrays.arraySumIsLarge:([I)V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 25)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Arrays.arraySumIsLarge!([I:])V" (control
    :coverage (
      :"jpamb.cases.Arrays.arraySumIsLarge:([I)V" (coverage
        :reachable (0 1 2 3 4 5 6 7 16 17 18 19 20 21)
      )
    )
    :results ("assertion error")
  )
  :"jpamb.cases.Arrays.arraySumIsLargeInt!(0)V" (control
    :coverage (
      :"jpamb.cases.Arrays.arraySumIsLargeInt:(I)V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 40)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Arrays.arraySumIsLargeInt!(1)V" (control
    :coverage (
      :"jpamb.cases.Arrays.arraySumIsLargeInt:(I)V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 40)
      )
    )
    :results ("assertion error")
  )
  :"jpamb.cases.Arrays.binarySearch!(3)V" (control
    :coverage (
      :"jpamb.cases.Arrays.binarySearch:(I)V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 47 48 49 50 51 52 53 54 57 58 59 60 61 62 63 64)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Arrays.binarySearch!(6)V" (control
    :coverage (
      :"jpamb.cases.Arrays.binarySearch:(I)V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64)
      )
    )
    :results ("assertion error")
  )
  :"jpamb.cases.Calls.allPrimesArePositive!(-1)V" (control
    :coverage (
      :"jpamb.cases.Calls.allPrimesArePositive:(I)V" (coverage
        :reachable (0 1)
      )
      :"jpamb.cases.Calls.generatePrimeArray:(I)[I" (coverage
        :reachable (0 1 2 3 4)
      )
    )
    :results ("assertion error")
  )
  :"jpamb.cases.Calls.allPrimesArePositive!(0)V" (control
    :coverage (
      :"jpamb.cases.Calls.allPrimesArePositive:(I)V" (coverage
        :reachable (0 1)
      )
      :"jpamb.cases.Calls.generatePrimeArray:(I)[I" (coverage
        :reachable (0 1 2 3 8 9 10 11 12 13 14)
      )
    )
    :results ("out of bounds")
  )
  :"jpamb.cases.Calls.allPrimesArePositive!(100)V" (control
    :coverage (
      :"jpamb.cases.Calls.allPrimesArePositive:(I)V" (coverage
        :reachable (0 1)
      )
      :"jpamb.cases.Calls.generatePrimeArray:(I)[I" (coverage
        :reachable (0 1 2 3 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 56 57 58 59 60 61 62 63 64)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Calls.callsAssertFalse!()V" (control
    :coverage (
      :"jpamb.cases.Calls.assertFalse:()V" (coverage
        :reachable (0 1 2)
      )
      :"jpamb.cases.Calls.callsAssertFalse:()V" (coverage
        :reachable (0)
      )
    )
    :results ("assertion error")
  )
  :"jpamb.cases.Calls.callsAssertFib!(0)V" (control
    :coverage (
      :"jpamb.cases.Calls.callsAssertFib:(I)V" (coverage
        :reachable (0 1 2 3 4 5 6)
      )
      :"jpamb.cases.Calls.fib:(I)I" (coverage
        :reachable (0 1 2 3 8 9 13 14)
      )
    )
    :results ("assertion error")
  )
  :"jpamb.cases.Calls.callsAssertFib!(8)V" (control
    :coverage (
      :"jpamb.cases.Calls.callsAssertFib:(I)V" (coverage
        :reachable (0 1 2 3)
      )
      :"jpamb.cases.Calls.fib:(I)I" (coverage
        :reachable (0 1 2 3 8 9 10 11 12 15 16 17 18)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Calls.callsAssertIf!(false)V" (control
    :coverage (
      :"jpamb.cases.Calls.assertFalse:()V" (coverage
        :reachable (0 1 2)
      )
      :"jpamb.cases.Calls.assertIf:(Z)V" (coverage
        :reachable (0 1 4)
      )
      :"jpamb.cases.Calls.callsAssertIf:(Z)V" (coverage
        :reachable (0 1)
      )
    )
    :results ("assertion error")
  )
  :"jpamb.cases.Calls.callsAssertIf!(true)V" (control
    :coverage (
      :"jpamb.cases.Calls.assertIf:(Z)V" (coverage
        :reachable (0 1 2 3 5)
      )
      :"jpamb.cases.Calls.assertTrue:()V" (coverage
        :reachable (0)
      )
      :"jpamb.cases.Calls.callsAssertIf:(Z)V" (coverage
        :reachable (0 1 2)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Calls.callsAssertIfWithTrue!()V" (control
    :coverage (
      :"jpamb.cases.Calls.assertIf:(Z)V" (coverage
        :reachable (0 1 2 3 5)
      )
      :"jpamb.cases.Calls.assertTrue:()V" (coverage
        :reachable (0)
      )
      :"jpamb.cases.Calls.callsAssertIfWithTrue:()V" (coverage
        :reachable (0 1 2)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Calls.callsAssertTrue!()V" (control
    :coverage (
      :"jpamb.cases.Calls.assertTrue:()V" (coverage
        :reachable (0)
      )
      :"jpamb.cases.Calls.callsAssertTrue:()V" (coverage
        :reachable (0 1)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Dependent.badNormalizedDistance!(0, 0)I" (control
    :coverage (
      :"jpamb.cases.Dependent.badNormalizedDistance:(II)I" (coverage
        :reachable (0 1 2 3 4 5 9 10 14 15 16 17 18 19)
      )
    )
    :results ("divide by zero")
  )
  :"jpamb.cases.Dependent.badNormalizedDistance!(1, 1)I" (control
    :coverage (
      :"jpamb.cases.Dependent.badNormalizedDistance:(II)I" (coverage
        :reachable (0 1 2 3 4 5 9 10 14 15 16 17 18 19 20)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Dependent.divisionLoop!(0)V" (control
    :coverage (
      :"jpamb.cases.Dependent.divisionLoop:(I)V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 20)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Dependent.divisionLoop!(1024)V" (control
    :coverage (
      :"jpamb.cases.Dependent.divisionLoop:(I)V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 20)
      )
    )
    :results ("assertion error")
  )
  :"jpamb.cases.Dependent.normalizedDistance!(0, 0)I" (control
    :coverage (
      :"jpamb.cases.Dependent.normalizedDistance:(II)I" (coverage
        :reachable (0 1 2 3 4 5 6 7)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Dependent.safeDivByN!(0)I" (control
    :coverage (
      :"jpamb.cases.Dependent.safeDivByN:(I)I" (coverage
        :reachable (0 1 6 7)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Loops.decrementLoop!(7)V" (control
    :coverage (
      :"jpamb.cases.Loops.decrementLoop:(I)V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 16)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Loops.decrementLoop!(8)V" (control
    :coverage (
      :"jpamb.cases.Loops.decrementLoop:(I)V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 16)
      )
    )
    :results ("assertion error")
  )
  :"jpamb.cases.Loops.forever!()V" (control
    :coverage (
      :"jpamb.cases.Loops.forever:()V" (coverage
        :reachable (0)
      )
    )
    :results (*)
  )
  :"jpamb.cases.Loops.multiplicationLoop!(10)V" (control
    :coverage (
      :"jpamb.cases.Loops.multiplicationLoop:(I)V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 20)
      )
    )
    :results ("assertion error")
  )
  :"jpamb.cases.Loops.multiplicationLoop!(9)V" (control
    :coverage (
      :"jpamb.cases.Loops.multiplicationLoop:(I)V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 20)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Loops.nestedLoop!(10)V" (control
    :coverage (
      :"jpamb.cases.Loops.nestedLoop:(I)V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 24)
      )
    )
    :results ("assertion error")
  )
  :"jpamb.cases.Loops.nestedLoop!(9)V" (control
    :coverage (
      :"jpamb.cases.Loops.nestedLoop:(I)V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 24)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Loops.neverAsserts!()V" (control
    :coverage (
      :"jpamb.cases.Loops.neverAsserts:()V" (coverage
        :reachable (0 1 2 3 4)
      )
    )
    :results (*)
  )
  :"jpamb.cases.Loops.neverDivides!()I" (control
    :coverage (
      :"jpamb.cases.Loops.neverDivides:()I" (coverage
        :reachable (0 1 2 3 4)
      )
    )
    :results (*)
  )
  :"jpamb.cases.Loops.terminates!()V" (control
    :coverage (
      :"jpamb.cases.Loops.terminates:()V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 10 11 12)
      )
    )
    :results ("assertion error")
  )
  :"jpamb.cases.MagicConstants.computedIndex!(0)I" (control
    :coverage (
      :"jpamb.cases.MagicConstants.computedIndex:(I)I" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 15 16)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.MagicConstants.computedIndex!(5)I" (control
    :coverage (
      :"jpamb.cases.MagicConstants.computedIndex:(I)I" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 13)
      )
    )
    :results ("out of bounds")
  )
  :"jpamb.cases.MagicConstants.derivedNull!(0)I" (control
    :coverage (
      :"jpamb.cases.MagicConstants.derivedNull:(I)I" (coverage
        :reachable (0 1 2 3 4 5 6 7 10 11 12 13)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.MagicConstants.derivedNull!(50)I" (control
    :coverage (
      :"jpamb.cases.MagicConstants.derivedNull:(I)I" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12)
      )
    )
    :results ("null pointer")
  )
  :"jpamb.cases.MagicConstants.loopAndEquality!(39)V" (control
    :coverage (
      :"jpamb.cases.MagicConstants.loopAndEquality:(I)V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 17)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.MagicConstants.loopAndEquality!(40)V" (control
    :coverage (
      :"jpamb.cases.MagicConstants.loopAndEquality:(I)V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 13 17)
      )
    )
    :results ("assertion error")
  )
  :"jpamb.cases.MagicConstants.narrowEquality!(123456788)V" (control
    :coverage (
      :"jpamb.cases.MagicConstants.narrowEquality:(I)V" (coverage
        :reachable (0 1 2 3 4 9)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.MagicConstants.narrowEquality!(123456789)V" (control
    :coverage (
      :"jpamb.cases.MagicConstants.narrowEquality:(I)V" (coverage
        :reachable (0 1 2 3 4 5)
      )
    )
    :results ("assertion error")
  )
  :"jpamb.cases.MagicConstants.rangeCondition!(1004)V" (control
    :coverage (
      :"jpamb.cases.MagicConstants.rangeCondition:(I)V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 15)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.MagicConstants.rangeCondition!(1005)V" (control
    :coverage (
      :"jpamb.cases.MagicConstants.rangeCondition:(I)V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11)
      )
    )
    :results ("assertion error")
  )
  :"jpamb.cases.MagicConstants.squareThreshold!(25)V" (control
    :coverage (
      :"jpamb.cases.MagicConstants.squareThreshold:(I)V" (coverage
        :reachable (0 1 2 3 4 5 6 7)
      )
    )
    :results ("assertion error")
  )
  :"jpamb.cases.MagicConstants.squareThreshold!(4)V" (control
    :coverage (
      :"jpamb.cases.MagicConstants.squareThreshold:(I)V" (coverage
        :reachable (0 1 2 3 4 5 6 11)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.MagicConstants.squaredDivisor!(10)I" (control
    :coverage (
      :"jpamb.cases.MagicConstants.squaredDivisor:(I)I" (coverage
        :reachable (0 1 2 3 4 5 6)
      )
    )
    :results ("divide by zero")
  )
  :"jpamb.cases.MagicConstants.squaredDivisor!(3)I" (control
    :coverage (
      :"jpamb.cases.MagicConstants.squaredDivisor:(I)I" (coverage
        :reachable (0 1 2 3 4 5 6 7)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.MagicConstants.sumReachesTarget!(1)V" (control
    :coverage (
      :"jpamb.cases.MagicConstants.sumReachesTarget:(I)V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 19)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.MagicConstants.sumReachesTarget!(42)V" (control
    :coverage (
      :"jpamb.cases.MagicConstants.sumReachesTarget:(I)V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9)
      )
    )
    :results ("assertion error")
  )
  :"jpamb.cases.MagicConstants.unreachableRange!(101)V" (control
    :coverage (
      :"jpamb.cases.MagicConstants.unreachableRange:(I)V" (coverage
        :reachable (0 1 2 3 4 5 12)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Simple.assertBoolean!(false)V" (control
    :coverage (
      :"jpamb.cases.Simple.assertBoolean:(Z)V" (coverage
        :reachable (0 1 2 3 4)
      )
    )
    :results ("assertion error")
  )
  :"jpamb.cases.Simple.assertBoolean!(true)V" (control
    :coverage (
      :"jpamb.cases.Simple.assertBoolean:(Z)V" (coverage
        :reachable (0 1 2 3 8)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Simple.assertFalse!()V" (control
    :coverage (
      :"jpamb.cases.Simple.assertFalse:()V" (coverage
        :reachable (0 1 2)
      )
    )
    :results ("assertion error")
  )
  :"jpamb.cases.Simple.assertInteger!(0)V" (control
    :coverage (
      :"jpamb.cases.Simple.assertInteger:(I)V" (coverage
        :reachable (0 1 2 3 4)
      )
    )
    :results ("assertion error")
  )
  :"jpamb.cases.Simple.assertInteger!(1)V" (control
    :coverage (
      :"jpamb.cases.Simple.assertInteger:(I)V" (coverage
        :reachable (0 1 2 3 8)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Simple.assertPositive!(-1)V" (control
    :coverage (
      :"jpamb.cases.Simple.assertPositive:(I)V" (coverage
        :reachable (0 1 2 3 4)
      )
    )
    :results ("assertion error")
  )
  :"jpamb.cases.Simple.assertPositive!(1)V" (control
    :coverage (
      :"jpamb.cases.Simple.assertPositive:(I)V" (coverage
        :reachable (0 1 2 3 8)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Simple.assertTrue!()V" (control
    :coverage (
      :"jpamb.cases.Simple.assertTrue:()V" (coverage
        :reachable (0)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Simple.checkBeforeAssert!(-1)V" (control
    :coverage (
      :"jpamb.cases.Simple.checkBeforeAssert:(I)V" (coverage
        :reachable (0 1 3 4 5 6 7 8 9)
      )
    )
    :results ("assertion error")
  )
  :"jpamb.cases.Simple.checkBeforeAssert!(0)V" (control
    :coverage (
      :"jpamb.cases.Simple.checkBeforeAssert:(I)V" (coverage
        :reachable (0 1 2)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Simple.checkBeforeDivideByN2!(0)I" (control
    :coverage (
      :"jpamb.cases.Simple.checkBeforeDivideByN2:(I)I" (coverage
        :reachable (0 1 6 7 8 9 10 15 16)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Simple.checkBeforeDivideByN!(0)I" (control
    :coverage (
      :"jpamb.cases.Simple.checkBeforeDivideByN:(I)I" (coverage
        :reachable (0 1 2 3 4)
      )
    )
    :results ("assertion error")
  )
  :"jpamb.cases.Simple.checkBeforeDivideByN!(1)I" (control
    :coverage (
      :"jpamb.cases.Simple.checkBeforeDivideByN:(I)I" (coverage
        :reachable (0 1 2 3 8 9 10 11)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Simple.divideByN!(0)I" (control
    :coverage (
      :"jpamb.cases.Simple.divideByN:(I)I" (coverage
        :reachable (0 1 2)
      )
    )
    :results ("divide by zero")
  )
  :"jpamb.cases.Simple.divideByN!(1)I" (control
    :coverage (
      :"jpamb.cases.Simple.divideByN:(I)I" (coverage
        :reachable (0 1 2 3)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Simple.divideByNMinus10054203!(0)I" (control
    :coverage (
      :"jpamb.cases.Simple.divideByNMinus10054203:(I)I" (coverage
        :reachable (0 1 2 3 4 5)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Simple.divideByNMinus10054203!(10054203)I" (control
    :coverage (
      :"jpamb.cases.Simple.divideByNMinus10054203:(I)I" (coverage
        :reachable (0 1 2 3 4)
      )
    )
    :results ("divide by zero")
  )
  :"jpamb.cases.Simple.divideByZero!()I" (control
    :coverage (
      :"jpamb.cases.Simple.divideByZero:()I" (coverage
        :reachable (0 1 2)
      )
    )
    :results ("divide by zero")
  )
  :"jpamb.cases.Simple.divideZeroByZero!(0, 0)I" (control
    :coverage (
      :"jpamb.cases.Simple.divideZeroByZero:(II)I" (coverage
        :reachable (0 1 2)
      )
    )
    :results ("divide by zero")
  )
  :"jpamb.cases.Simple.divideZeroByZero!(0, 1)I" (control
    :coverage (
      :"jpamb.cases.Simple.divideZeroByZero:(II)I" (coverage
        :reachable (0 1 2 3)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Simple.doNothing!()V" (control
    :coverage (
      :"jpamb.cases.Simple.doNothing:()V" (coverage
        :reachable (0)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Simple.earlyReturn!()I" (control
    :coverage (
      :"jpamb.cases.Simple.earlyReturn:()I" (coverage
        :reachable (0 1)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Simple.justAdd!(1, 2)I" (control
    :coverage (
      :"jpamb.cases.Simple.justAdd:(II)I" (coverage
        :reachable (0 1 2 3)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Simple.justMulitply!(1, 2)I" (control
    :coverage (
      :"jpamb.cases.Simple.justMulitply:(II)I" (coverage
        :reachable (0 1 2 3)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Simple.justReturn!()I" (control
    :coverage (
      :"jpamb.cases.Simple.justReturn:()I" (coverage
        :reachable (0 1)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Simple.justReturnNothing!()V" (control
    :coverage (
      :"jpamb.cases.Simple.justReturnNothing:()V" (coverage
        :reachable (0)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Simple.multiError!(false)I" (control
    :coverage (
      :"jpamb.cases.Simple.multiError:(Z)I" (coverage
        :reachable (0 1 2 3 4)
      )
    )
    :results ("assertion error")
  )
  :"jpamb.cases.Simple.multiError!(true)I" (control
    :coverage (
      :"jpamb.cases.Simple.multiError:(Z)I" (coverage
        :reachable (0 1 2 3 8 9 10)
      )
    )
    :results ("divide by zero")
  )
  :"jpamb.cases.Strings.sayHello!(s'hello')V" (control
    :coverage (
      :"jpamb.cases.Strings.sayHello:(Ljava/lang/String;)V" (coverage
        :reachable (0 1 2 3 4 5 10)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Strings.sayHello!(s'not hello')V" (control
    :coverage (
      :"jpamb.cases.Strings.sayHello:(Ljava/lang/String;)V" (coverage
        :reachable (0 1 2 3 4 5 6)
      )
    )
    :results ("assertion error")
  )
  :"jpamb.cases.Tricky.collatz!(0)V" (control
    :coverage (
      :"jpamb.cases.Tricky.collatz:(I)V" (coverage
        :reachable (0 1 2 3 4)
      )
    )
    :results ("assertion error")
  )
  :"jpamb.cases.Tricky.collatz!(24)V" (control
    :coverage (
      :"jpamb.cases.Tricky.collatz:(I)V" (coverage
        :reachable (0 1 2 3 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.advanced.CWE470.strict_safe_dispatcher!(s'Any')V" (control
    :coverage (
      :"jpamb.cases.advanced.CWE470.strict_safe_dispatcher:(Ljava/lang/String;)V" (coverage
        :reachable (0 1 2 3 4)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Arrays.arrayContent:()V" (control
    :coverage (
      :"jpamb.cases.Arrays.arrayContent:()V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 39 40 41)
      )
    )
    :results ("assertion error")
  )
  :"jpamb.cases.Arrays.arrayContentAboveMinus13:()V" (control
    :coverage (
      :"jpamb.cases.Arrays.arrayContentAboveMinus13:()V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 40 41 42)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Arrays.arrayInBounds:()V" (control
    :coverage (
      :"jpamb.cases.Arrays.arrayInBounds:()V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Arrays.arrayIndexValue:(I)V" (control
    :coverage (
      :"jpamb.cases.Arrays.arrayIndexValue:(I)V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 52)
      )
    )
    :results ("assertion error" ok)
  )
  :"jpamb.cases.Arrays.arrayIsNull:()V" (control
    :coverage (
      :"jpamb.cases.Arrays.arrayIsNull:()V" (coverage
        :reachable (0 1 2 3 4 5)
      )
    )
    :results ("null pointer")
  )
  :"jpamb.cases.Arrays.arrayIsNullLength:()V" (control
    :coverage (
      :"jpamb.cases.Arrays.arrayIsNullLength:()V" (coverage
        :reachable (0 1 2 3 4 5)
      )
    )
    :results ("null pointer")
  )
  :"jpamb.cases.Arrays.arrayLength:()V" (control
    :coverage (
      :"jpamb.cases.Arrays.arrayLength:()V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 21)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Arrays.arrayLoop:(I)V" (control
    :coverage (
      :"jpamb.cases.Arrays.arrayLoop:(I)V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16)
      )
    )
    :results ("assertion error" ok)
  )
  :"jpamb.cases.Arrays.arrayNotEmpty:([I)V" (control
    :coverage (
      :"jpamb.cases.Arrays.arrayNotEmpty:([I)V" (coverage
        :reachable (0 1 2 3 4 5 9)
      )
    )
    :results ("assertion error" ok)
  )
  :"jpamb.cases.Arrays.arrayOutOfBounds:()V" (control
    :coverage (
      :"jpamb.cases.Arrays.arrayOutOfBounds:()V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 13 14)
      )
    )
    :results ("out of bounds")
  )
  :"jpamb.cases.Arrays.arraySometimesNull:(I)V" (control
    :coverage (
      :"jpamb.cases.Arrays.arraySometimesNull:(I)V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15)
      )
    )
    :results ("null pointer" "out of bounds")
  )
  :"jpamb.cases.Arrays.arraySpellsHello:([C)V" (control
    :coverage (
      :"jpamb.cases.Arrays.arraySpellsHello:([C)V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 31)
      )
    )
    :results ("assertion error" ok "out of bounds")
  )
  :"jpamb.cases.Arrays.arraySumIsLarge:([I)V" (control
    :coverage (
      :"jpamb.cases.Arrays.arraySumIsLarge:([I)V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 25)
      )
    )
    :results ("assertion error" ok)
  )
  :"jpamb.cases.Arrays.arraySumIsLargeInt:(I)V" (control
    :coverage (
      :"jpamb.cases.Arrays.arraySumIsLargeInt:(I)V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 40)
      )
    )
    :results ("assertion error" ok)
  )
  :"jpamb.cases.Arrays.binarySearch:(I)V" (control
    :coverage (
      :"jpamb.cases.Arrays.binarySearch:(I)V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64)
      )
    )
    :results ("assertion error" ok)
  )
  :"jpamb.cases.Calls.allPrimesArePositive:(I)V" (control
    :coverage (
      :"jpamb.cases.Calls.allPrimesArePositive:(I)V" (coverage
        :reachable (0 1)
      )
      :"jpamb.cases.Calls.generatePrimeArray:(I)[I" (coverage
        :reachable (0 1 2 3 4 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 56 57 58 59 60 61 62 63 64)
      )
    )
    :results ("assertion error" ok "out of bounds")
  )
  :"jpamb.cases.Calls.callsAssertFalse:()V" (control
    :coverage (
      :"jpamb.cases.Calls.assertFalse:()V" (coverage
        :reachable (0 1 2)
      )
      :"jpamb.cases.Calls.callsAssertFalse:()V" (coverage
        :reachable (0)
      )
    )
    :results ("assertion error")
  )
  :"jpamb.cases.Calls.callsAssertFib:(I)V" (control
    :coverage (
      :"jpamb.cases.Calls.callsAssertFib:(I)V" (coverage
        :reachable (0 1 2 3 4 5 6)
      )
      :"jpamb.cases.Calls.fib:(I)I" (coverage
        :reachable (0 1 2 3 8 9 10 11 12 13 14 15 16 17 18)
      )
    )
    :results ("assertion error" ok)
  )
  :"jpamb.cases.Calls.callsAssertIf:(Z)V" (control
    :coverage (
      :"jpamb.cases.Calls.assertFalse:()V" (coverage
        :reachable (0 1 2)
      )
      :"jpamb.cases.Calls.assertIf:(Z)V" (coverage
        :reachable (0 1 2 3 4 5)
      )
      :"jpamb.cases.Calls.callsAssertIf:(Z)V" (coverage
        :reachable (0 1 2)
      )
      :"jpamb.cases.Calls.assertTrue:()V" (coverage
        :reachable (0)
      )
    )
    :results ("assertion error" ok)
  )
  :"jpamb.cases.Calls.callsAssertIfWithTrue:()V" (control
    :coverage (
      :"jpamb.cases.Calls.assertIf:(Z)V" (coverage
        :reachable (0 1 2 3 5)
      )
      :"jpamb.cases.Calls.assertTrue:()V" (coverage
        :reachable (0)
      )
      :"jpamb.cases.Calls.callsAssertIfWithTrue:()V" (coverage
        :reachable (0 1 2)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Calls.callsAssertTrue:()V" (control
    :coverage (
      :"jpamb.cases.Calls.assertTrue:()V" (coverage
        :reachable (0)
      )
      :"jpamb.cases.Calls.callsAssertTrue:()V" (coverage
        :reachable (0 1)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Dependent.badNormalizedDistance:(II)I" (control
    :coverage (
      :"jpamb.cases.Dependent.badNormalizedDistance:(II)I" (coverage
        :reachable (0 1 2 3 4 5 9 10 14 15 16 17 18 19 20)
      )
    )
    :results ("divide by zero" ok)
  )
  :"jpamb.cases.Dependent.divisionLoop:(I)V" (control
    :coverage (
      :"jpamb.cases.Dependent.divisionLoop:(I)V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 20)
      )
    )
    :results ("assertion error" ok)
  )
  :"jpamb.cases.Dependent.normalizedDistance:(II)I" (control
    :coverage (
      :"jpamb.cases.Dependent.normalizedDistance:(II)I" (coverage
        :reachable (0 1 2 3 4 5 6 7)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Dependent.safeDivByN:(I)I" (control
    :coverage (
      :"jpamb.cases.Dependent.safeDivByN:(I)I" (coverage
        :reachable (0 1 6 7)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Loops.decrementLoop:(I)V" (control
    :coverage (
      :"jpamb.cases.Loops.decrementLoop:(I)V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 16)
      )
    )
    :results ("assertion error" ok)
  )
  :"jpamb.cases.Loops.forever:()V" (control
    :coverage (
      :"jpamb.cases.Loops.forever:()V" (coverage
        :reachable (0)
      )
    )
    :results (*)
  )
  :"jpamb.cases.Loops.multiplicationLoop:(I)V" (control
    :coverage (
      :"jpamb.cases.Loops.multiplicationLoop:(I)V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 20)
      )
    )
    :results ("assertion error" ok)
  )
  :"jpamb.cases.Loops.nestedLoop:(I)V" (control
    :coverage (
      :"jpamb.cases.Loops.nestedLoop:(I)V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 24)
      )
    )
    :results ("assertion error" ok)
  )
  :"jpamb.cases.Loops.neverAsserts:()V" (control
    :coverage (
      :"jpamb.cases.Loops.neverAsserts:()V" (coverage
        :reachable (0 1 2 3 4)
      )
    )
    :results (*)
  )
  :"jpamb.cases.Loops.neverDivides:()I" (control
    :coverage (
      :"jpamb.cases.Loops.neverDivides:()I" (coverage
        :reachable (0 1 2 3 4)
      )
    )
    :results (*)
  )
  :"jpamb.cases.Loops.terminates:()V" (control
    :coverage (
      :"jpamb.cases.Loops.terminates:()V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 10 11 12)
      )
    )
    :results ("assertion error")
  )
  :"jpamb.cases.MagicConstants.computedIndex:(I)I" (control
    :coverage (
      :"jpamb.cases.MagicConstants.computedIndex:(I)I" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 13 15 16)
      )
    )
    :results (ok "out of bounds")
  )
  :"jpamb.cases.MagicConstants.derivedNull:(I)I" (control
    :coverage (
      :"jpamb.cases.MagicConstants.derivedNull:(I)I" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 13)
      )
    )
    :results ("null pointer" ok)
  )
  :"jpamb.cases.MagicConstants.loopAndEquality:(I)V" (control
    :coverage (
      :"jpamb.cases.MagicConstants.loopAndEquality:(I)V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 13 17)
      )
    )
    :results ("assertion error" ok)
  )
  :"jpamb.cases.MagicConstants.narrowEquality:(I)V" (control
    :coverage (
      :"jpamb.cases.MagicConstants.narrowEquality:(I)V" (coverage
        :reachable (0 1 2 3 4 5 9)
      )
    )
    :results ("assertion error" ok)
  )
  :"jpamb.cases.MagicConstants.rangeCondition:(I)V" (control
    :coverage (
      :"jpamb.cases.MagicConstants.rangeCondition:(I)V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 15)
      )
    )
    :results ("assertion error" ok)
  )
  :"jpamb.cases.MagicConstants.squareThreshold:(I)V" (control
    :coverage (
      :"jpamb.cases.MagicConstants.squareThreshold:(I)V" (coverage
        :reachable (0 1 2 3 4 5 6 7 11)
      )
    )
    :results ("assertion error" ok)
  )
  :"jpamb.cases.MagicConstants.squaredDivisor:(I)I" (control
    :coverage (
      :"jpamb.cases.MagicConstants.squaredDivisor:(I)I" (coverage
        :reachable (0 1 2 3 4 5 6 7)
      )
    )
    :results ("divide by zero" ok)
  )
  :"jpamb.cases.MagicConstants.sumReachesTarget:(I)V" (control
    :coverage (
      :"jpamb.cases.MagicConstants.sumReachesTarget:(I)V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 19)
      )
    )
    :results ("assertion error" ok)
  )
  :"jpamb.cases.MagicConstants.unreachableRange:(I)V" (control
    :coverage (
      :"jpamb.cases.MagicConstants.unreachableRange:(I)V" (coverage
        :reachable (0 1 2 3 4 5 12)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Simple.assertBoolean:(Z)V" (control
    :coverage (
      :"jpamb.cases.Simple.assertBoolean:(Z)V" (coverage
        :reachable (0 1 2 3 4 8)
      )
    )
    :results ("assertion error" ok)
  )
  :"jpamb.cases.Simple.assertFalse:()V" (control
    :coverage (
      :"jpamb.cases.Simple.assertFalse:()V" (coverage
        :reachable (0 1 2)
      )
    )
    :results ("assertion error")
  )
  :"jpamb.cases.Simple.assertInteger:(I)V" (control
    :coverage (
      :"jpamb.cases.Simple.assertInteger:(I)V" (coverage
        :reachable (0 1 2 3 4 8)
      )
    )
    :results ("assertion error" ok)
  )
  :"jpamb.cases.Simple.assertPositive:(I)V" (control
    :coverage (
      :"jpamb.cases.Simple.assertPositive:(I)V" (coverage
        :reachable (0 1 2 3 4 8)
      )
    )
    :results ("assertion error" ok)
  )
  :"jpamb.cases.Simple.assertTrue:()V" (control
    :coverage (
      :"jpamb.cases.Simple.assertTrue:()V" (coverage
        :reachable (0)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Simple.checkBeforeAssert:(I)V" (control
    :coverage (
      :"jpamb.cases.Simple.checkBeforeAssert:(I)V" (coverage
        :reachable (0 1 2 3 4 5 6 7 8 9)
      )
    )
    :results ("assertion error" ok)
  )
  :"jpamb.cases.Simple.checkBeforeDivideByN2:(I)I" (control
    :coverage (
      :"jpamb.cases.Simple.checkBeforeDivideByN2:(I)I" (coverage
        :reachable (0 1 6 7 8 9 10 15 16)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Simple.checkBeforeDivideByN:(I)I" (control
    :coverage (
      :"jpamb.cases.Simple.checkBeforeDivideByN:(I)I" (coverage
        :reachable (0 1 2 3 4 8 9 10 11)
      )
    )
    :results ("assertion error" ok)
  )
  :"jpamb.cases.Simple.divideByN:(I)I" (control
    :coverage (
      :"jpamb.cases.Simple.divideByN:(I)I" (coverage
        :reachable (0 1 2 3)
      )
    )
    :results ("divide by zero" ok)
  )
  :"jpamb.cases.Simple.divideByNMinus10054203:(I)I" (control
    :coverage (
      :"jpamb.cases.Simple.divideByNMinus10054203:(I)I" (coverage
        :reachable (0 1 2 3 4 5)
      )
    )
    :results ("divide by zero" ok)
  )
  :"jpamb.cases.Simple.divideByZero:()I" (control
    :coverage (
      :"jpamb.cases.Simple.divideByZero:()I" (coverage
        :reachable (0 1 2)
      )
    )
    :results ("divide by zero")
  )
  :"jpamb.cases.Simple.divideZeroByZero:(II)I" (control
    :coverage (
      :"jpamb.cases.Simple.divideZeroByZero:(II)I" (coverage
        :reachable (0 1 2 3)
      )
    )
    :results ("divide by zero" ok)
  )
  :"jpamb.cases.Simple.doNothing:()V" (control
    :coverage (
      :"jpamb.cases.Simple.doNothing:()V" (coverage
        :reachable (0)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Simple.earlyReturn:()I" (control
    :coverage (
      :"jpamb.cases.Simple.earlyReturn:()I" (coverage
        :reachable (0 1)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Simple.justAdd:(II)I" (control
    :coverage (
      :"jpamb.cases.Simple.justAdd:(II)I" (coverage
        :reachable (0 1 2 3)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Simple.justMulitply:(II)I" (control
    :coverage (
      :"jpamb.cases.Simple.justMulitply:(II)I" (coverage
        :reachable (0 1 2 3)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Simple.justReturn:()I" (control
    :coverage (
      :"jpamb.cases.Simple.justReturn:()I" (coverage
        :reachable (0 1)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Simple.justReturnNothing:()V" (control
    :coverage (
      :"jpamb.cases.Simple.justReturnNothing:()V" (coverage
        :reachable (0)
      )
    )
    :results (ok)
  )
  :"jpamb.cases.Simple.multiError:(Z)I" (control
    :coverage (
      :"jpamb.cases.Simple.multiError:(Z)I" (coverage
        :reachable (0 1 2 3 4 8 9 10)
      )
    )
    :results ("assertion error" "divide by zero")
  )
  :"jpamb.cases.Strings.sayHello:(Ljava/lang/String;)V" (control
    :coverage (
      :"jpamb.cases.Strings.sayHello:(Ljava/lang/String;)V" (coverage
        :reachable (0 1 2 3 4 5 6 10)
      )
    )
    :results ("assertion error" ok)
  )
  :"jpamb.cases.Tricky.collatz:(I)V" (control
    :coverage (
      :"jpamb.cases.Tricky.collatz:(I)V" (coverage
        :reachable (0 1 2 3 4 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26)
      )
    )
    :results ("assertion error" ok)
  )
  :"jpamb.cases.advanced.CWE470.strict_safe_dispatcher:(Ljava/lang/String;)V" (control
    :coverage (
      :"jpamb.cases.advanced.CWE470.strict_safe_dispatcher:(Ljava/lang/String;)V" (coverage
        :reachable (0 1 2 3 4)
      )
    )
    :results (ok)
  )
)