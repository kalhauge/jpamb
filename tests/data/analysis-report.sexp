(analysis-summary
  :config (analysis-config
    :cmd (syntactic-regex)
    :analysis (analysis-info
      :name syntaxer
      :version 1.0
      :group "Not The Rice Theorem Cookers"
      :tags (syntactic python)
      :system Linux-6.18.44-x86_64-with-glibc2.42
    )
    :experiments (
      :"jpamb.cases.Arrays.arrayContent:()V" ("assertion error")
      :"jpamb.cases.Arrays.arrayInBounds:()V" (ok)
      :"jpamb.cases.Arrays.arrayIsNull:()V" ("null pointer")
      :"jpamb.cases.Arrays.arrayIsNullLength:()V" ("null pointer")
      :"jpamb.cases.Arrays.arrayLength:()V" (ok)
      :"jpamb.cases.Arrays.arrayNotEmpty:([I)V" (ok "assertion error")
      :"jpamb.cases.Arrays.arrayOutOfBounds:()V" ("out of bounds")
      :"jpamb.cases.Arrays.arraySometimesNull:(I)V" ("out of bounds" "null pointer")
      :"jpamb.cases.Arrays.arraySpellsHello:([C)V" ("out of bounds" ok "assertion error")
      :"jpamb.cases.Arrays.arraySumIsLarge:([I)V" (ok "assertion error")
      :"jpamb.cases.Arrays.binarySearch:(I)V" (ok "assertion error")
      :"jpamb.cases.Calls.allPrimesArePositive:(I)V" ("out of bounds" ok "assertion error")
      :"jpamb.cases.Calls.callsAssertFalse:()V" ("assertion error")
      :"jpamb.cases.Calls.callsAssertFib:(I)V" (ok "assertion error")
      :"jpamb.cases.Calls.callsAssertIf:(Z)V" (ok "assertion error")
      :"jpamb.cases.Calls.callsAssertIfWithTrue:()V" (ok)
      :"jpamb.cases.Calls.callsAssertTrue:()V" (ok)
      :"jpamb.cases.Dependent.badNormalizedDistance:(II)I" ("divide by zero" ok)
      :"jpamb.cases.Dependent.divisionLoop:(I)V" (ok)
      :"jpamb.cases.Dependent.normalizedDistance:(II)I" (ok)
      :"jpamb.cases.Dependent.safeDivByN:(I)I" (ok)
      :"jpamb.cases.Loops.forever:()V" (*)
      :"jpamb.cases.Loops.neverAsserts:()V" (*)
      :"jpamb.cases.Loops.neverDivides:()I" (*)
      :"jpamb.cases.Loops.terminates:()V" ("assertion error")
      :"jpamb.cases.Simple.assertBoolean:(Z)V" (ok "assertion error")
      :"jpamb.cases.Simple.assertFalse:()V" ("assertion error")
      :"jpamb.cases.Simple.assertInteger:(I)V" (ok "assertion error")
      :"jpamb.cases.Simple.assertPositive:(I)V" (ok "assertion error")
      :"jpamb.cases.Simple.assertTrue:()V" (ok)
      :"jpamb.cases.Simple.checkBeforeAssert:(I)V" (ok "assertion error")
      :"jpamb.cases.Simple.checkBeforeDivideByN:(I)I" (ok "assertion error")
      :"jpamb.cases.Simple.checkBeforeDivideByN2:(I)I" (ok)
      :"jpamb.cases.Simple.divideByN:(I)I" ("divide by zero" ok)
      :"jpamb.cases.Simple.divideByNMinus10054203:(I)I" (ok "divide by zero")
      :"jpamb.cases.Simple.divideByZero:()I" ("divide by zero")
      :"jpamb.cases.Simple.divideZeroByZero:(II)I" ("divide by zero" ok)
      :"jpamb.cases.Simple.doNothing:()V" (ok)
      :"jpamb.cases.Simple.earlyReturn:()I" (ok)
      :"jpamb.cases.Simple.justAdd:(II)I" (ok)
      :"jpamb.cases.Simple.justMulitply:(II)I" (ok)
      :"jpamb.cases.Simple.justReturn:()I" (ok)
      :"jpamb.cases.Simple.justReturnNothing:()V" (ok)
      :"jpamb.cases.Simple.multiError:(Z)I" ("divide by zero" "assertion error")
      :"jpamb.cases.Strings.sayHello:(Ljava/lang/String;)V" (ok "assertion error")
      :"jpamb.cases.Tricky.collatz:(I)V" (ok "assertion error")
    )
    :iterations 3
    :timeout 5.0
  )
  :results (
    :"jpamb.cases.Arrays.arrayContent:()V" ((analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 70571779
          :relative 1.2933954638438387
        )
        :calibrates (3620896 3561438)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 67485928
          :relative 1.291124509721665
        )
        :calibrates (3518390 3385895)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 54319824
          :relative 1.2240522522185755
        )
        :calibrates (3258830 3226560)
      ))
    :"jpamb.cases.Arrays.arrayInBounds:()V" ((analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 70464646
          :relative 1.3261559841739288
        )
        :calibrates (3373779 3276583)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 68222161
          :relative 1.302421839164026
        )
        :calibrates (3454317 3346070)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 54670348
          :relative 1.2224813281579172
        )
        :calibrates (3360851 3190042)
      ))
    :"jpamb.cases.Arrays.arrayIsNull:()V" ((analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 69705482
          :relative 1.3332614413398802
        )
        :calibrates (3193130 3278825)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 54230197
          :relative 1.2133719994291325
        )
        :calibrates (3278418 3357472)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 80322547
          :relative 1.3949237861409092
        )
        :calibrates (3238257 3232330)
      ))
    :"jpamb.cases.Arrays.arrayIsNullLength:()V" ((analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 75765845
          :relative 1.36635699623876
        )
        :calibrates (3230352 3288130)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 66936590
          :relative 1.2902007802799118
        )
        :calibrates (3383370 3479295)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 72325220
          :relative 1.323517296608148
        )
        :calibrates (3496358 3371202)
      ))
    :"jpamb.cases.Arrays.arrayLength:()V" ((analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 69127399
          :relative 1.316466811799042
        )
        :calibrates (3355249 3316096)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 69904273
          :relative 1.320191352289928
        )
        :calibrates (3446649 3242061)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 56845066
          :relative 1.2405046262862902
        )
        :calibrates (3242656 3291931)
      ))
    :"jpamb.cases.Arrays.arrayNotEmpty:([I)V" ((analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 75483679
          :relative 1.35872837807415
        )
        :calibrates (3289965 3319323)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 55804671
          :relative 1.224211907526463
        )
        :calibrates (3316147 3344074)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 55826768
          :relative 1.2155400686899172
        )
        :calibrates (3389491 3407746)
      ))
    :"jpamb.cases.Arrays.arrayOutOfBounds:()V" ((analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 75317810
          :relative 1.3576048183001208
        )
        :calibrates (3275246 3336602)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 55484106
          :relative 1.2256177394209555
        )
        :calibrates (3395090 3205471)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 56492299
          :relative 1.231934457972793
        )
        :calibrates (3362396 3261062)
      ))
    :"jpamb.cases.Arrays.arraySometimesNull:(I)V" ((analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 68830448
          :relative 1.3108111445294328
        )
        :calibrates (3396964 3332794)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 55592962
          :relative 1.2272506693363188
        )
        :calibrates (3332704 3255987)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 55192739
          :relative 1.2273674649004325
        )
        :calibrates (3332651 3206848)
      ))
    :"jpamb.cases.Arrays.arraySpellsHello:([C)V" ((analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 55070546
          :relative 1.2211100203279113
        )
        :calibrates (3310399 3309317)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 56430436
          :relative 1.217152691746284
        )
        :calibrates (3471814 3373458)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 54910865
          :relative 1.2267549295066364
        )
        :calibrates (3289297 3225987)
      ))
    :"jpamb.cases.Arrays.arraySumIsLarge:([I)V" ((analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 72277160
          :relative 1.3271894797421984
        )
        :calibrates (3350294 3454917)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 68523130
          :relative 1.3122032797083603
        )
        :calibrates (3371280 3306989)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 55677571
          :relative 1.2137154809103785
        )
        :calibrates (3512213 3295399)
      ))
    :"jpamb.cases.Arrays.binarySearch:(I)V" ((analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 69141325
          :relative 1.3006349272686488
        )
        :calibrates (3578252 3342173)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 69848434
          :relative 1.3108922028371577
        )
        :calibrates (3430575 3397440)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 55593659
          :relative 1.216704001442952
        )
        :calibrates (3396933 3353805)
      ))
    :"jpamb.cases.Calls.allPrimesArePositive:(I)V" ((analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 71068827
          :relative 1.3148337108400305
        )
        :calibrates (3508130 3376418)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 69898939
          :relative 1.324317777713504
        )
        :calibrates (3358277 3266676)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 55131386
          :relative 1.21025171698021
        )
        :calibrates (3561996 3232812)
      ))
    :"jpamb.cases.Calls.callsAssertFalse:()V" ((analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 73097403
          :relative 1.334888312864088
        )
        :calibrates (3490018 3271491)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 56228532
          :relative 1.2383906687029145
        )
        :calibrates (3295083 3200170)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 54188459
          :relative 1.2122792344579674
        )
        :calibrates (3391780 3255708)
      ))
    :"jpamb.cases.Calls.callsAssertFib:(I)V" ((analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 73025494
          :relative 1.3368984967989577
        )
        :calibrates (3447745 3275919)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 80870887
          :relative 1.3832212982141598
        )
        :calibrates (3273960 3418733)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 55382076
          :relative 1.2241504641162715
        )
        :calibrates (3344997 3265723)
      ))
    :"jpamb.cases.Calls.callsAssertIf:(Z)V" ((analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 68886792
          :relative 1.3174845722986617
        )
        :calibrates (3327443 3305120)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 56384904
          :relative 1.2331836800071132
        )
        :calibrates (3355077 3236801)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 58437122
          :relative 1.2467733846962457
        )
        :calibrates (3390033 3231300)
      ))
    :"jpamb.cases.Calls.callsAssertIfWithTrue:()V" ((analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 55442223
          :relative 1.2273848563365952
        )
        :calibrates (3402541 3166255)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 70494540
          :relative 1.3310349640723687
        )
        :calibrates (3439405 3139453)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 56130416
          :relative 1.2155655472721292
        )
        :calibrates (3484349 3349458)
      ))
    :"jpamb.cases.Calls.callsAssertTrue:()V" ((analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 73222921
          :relative 1.3429664369182395
        )
        :calibrates (3400908 3247392)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 57033652
          :relative 1.2470789401825286
        )
        :calibrates (3306075 3151690)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 55261427
          :relative 1.224107779436149
        )
        :calibrates (3361640 3235327)
      ))
    :"jpamb.cases.Dependent.badNormalizedDistance:(II)I" ((analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 69660248
          :relative 1.314163023076067
        )
        :calibrates (3486736 3271790)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 56085771
          :relative 1.2426500145420851
        )
        :calibrates (3257147 3158385)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 54719091
          :relative 1.2277563527136575
        )
        :calibrates (3279463 3198113)
      ))
    :"jpamb.cases.Dependent.divisionLoop:(I)V" ((analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 68595572
          :relative 1.3205110922925845
        )
        :calibrates (3273660 3284998)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 55163648
          :relative 1.226927228213766
        )
        :calibrates (3394487 3148194)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 55248422
          :relative 1.2330339336838074
        )
        :calibrates (3249800 3211441)
      ))
    :"jpamb.cases.Dependent.normalizedDistance:(II)I" ((analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 69686081
          :relative 1.3064992339315098
        )
        :calibrates (3534185 3347215)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 56695552
          :relative 1.246061141235125
        )
        :calibrates (3290347 3144198)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 55367218
          :relative 1.236945244459671
        )
        :calibrates (3215559 3201521)
      ))
    :"jpamb.cases.Dependent.safeDivByN:(I)I" ((analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 72243203
          :relative 1.3349473607610183
        )
        :calibrates (3372068 3309519)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 56023783
          :relative 1.2407812630340345
        )
        :calibrates (3251827 3184249)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 54467929
          :relative 1.2284256199602044
        )
        :calibrates (3257958 3179957)
      ))
    :"jpamb.cases.Loops.forever:()V" ((analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 55625241
          :relative 1.220526605730166
        )
        :calibrates (3361429 3333952)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 55911987
          :relative 1.2301432626497102
        )
        :calibrates (3397883 3184629)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 55204028
          :relative 1.2237874778640574
        )
        :calibrates (3332818 3262159)
      ))
    :"jpamb.cases.Loops.neverAsserts:()V" ((analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 68016550
          :relative 1.2999984270624476
        )
        :calibrates (3381107 3436723)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 56236000
          :relative 1.2447313259402195
        )
        :calibrates (3208567 3193395)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 56223113
          :relative 1.241012980207236
        )
        :calibrates (3194062 3261468)
      ))
    :"jpamb.cases.Loops.neverDivides:()I" ((analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 69268793
          :relative 1.302527162990526
        )
        :calibrates (3516364 3386677)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 69076627
          :relative 1.3333786452464906
        )
        :calibrates (3173055 3238782)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 55668084
          :relative 1.2244589026650814
        )
        :calibrates (3422233 3217909)
      ))
    :"jpamb.cases.Loops.terminates:()V" ((analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 68237143
          :relative 1.307909751605267
        )
        :calibrates (3385649 3330821)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 61373317
          :relative 1.2669283143836458
        )
        :calibrates (3197375 3441298)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 56315702
          :relative 1.2339993473866258
        )
        :calibrates (3298195 3273239)
      ))
    :"jpamb.cases.Simple.assertBoolean:(Z)V" ((analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 72967331
          :relative 1.3298990377174003
        )
        :calibrates (3409345 3418119)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 71022331
          :relative 1.311082531495931
        )
        :calibrates (3634820 3304907)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 55643891
          :relative 1.2099232366547992
        )
        :calibrates (3563465 3299697)
      ))
    :"jpamb.cases.Simple.assertFalse:()V" ((analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 69802867
          :relative 1.2978906675390736
        )
        :calibrates (3516625 3514302)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 56869508
          :relative 1.2354874994091418
        )
        :calibrates (3346865 3266492)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 55308256
          :relative 1.2234097477059003
        )
        :calibrates (3398742 3214436)
      ))
    :"jpamb.cases.Simple.assertInteger:(I)V" ((analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 68334044
          :relative 1.3041248836657802
        )
        :calibrates (3450738 3334143)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 55291720
          :relative 1.2209874568870736
        )
        :calibrates (3461328 3186850)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 67635920
          :relative 1.3179404686152822
        )
        :calibrates (3278459 3226835)
      ))
    :"jpamb.cases.Simple.assertPositive:(I)V" ((analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 56582591
          :relative 1.220926564562013
        )
        :calibrates (3388274 3416070)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 55437159
          :relative 1.2339875668311062
        )
        :calibrates (3264219 3204874)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 55566709
          :relative 1.209897846916013
        )
        :calibrates (3589254 3264789)
      ))
    :"jpamb.cases.Simple.assertTrue:()V" ((analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 69717471
          :relative 1.3039010472536179
        )
        :calibrates (3444564 3481246)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 55530351
          :relative 1.2309588662630815
        )
        :calibrates (3290931 3234385)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 55633377
          :relative 1.2259802275885512
        )
        :calibrates (3378035 3234762)
      ))
    :"jpamb.cases.Simple.checkBeforeAssert:(I)V" ((analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 68370857
          :relative 1.314409304421014
        )
        :calibrates (3352909 3276758)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 56710330
          :relative 1.2273465512658366
        )
        :calibrates (3399502 3320132)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 56221867
          :relative 1.2387424933775109
        )
        :calibrates (3305817 3183407)
      ))
    :"jpamb.cases.Simple.checkBeforeDivideByN:(I)I" ((analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 56758454
          :relative 1.225905109215466
        )
        :calibrates (3410512 3337183)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 55927059
          :relative 1.222156890551602
        )
        :calibrates (3444436 3262051)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 56830662
          :relative 1.2401184425736496
        )
        :calibrates (3362405 3176338)
      ))
    :"jpamb.cases.Simple.checkBeforeDivideByN2:(I)I" ((analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 72283600
          :relative 1.3339348828682618
        )
        :calibrates (3381664 3319263)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 56239681
          :relative 1.2195708089332944
        )
        :calibrates (3423644 3360609)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 56224549
          :relative 1.2277065818897146
        )
        :calibrates (3504235 3152318)
      ))
    :"jpamb.cases.Simple.divideByN:(I)I" ((analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 70582016
          :relative 1.3024329142493436
        )
        :calibrates (3566654 3468784)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 55248411
          :relative 1.2114812923929048
        )
        :calibrates (3491838 3298142)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 54391197
          :relative 1.2191552243695032
        )
        :calibrates (3360000 3207550)
      ))
    :"jpamb.cases.Simple.divideByNMinus10054203:(I)I" ((analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 55478812
          :relative 1.2209291663360016
        )
        :calibrates (3306256 3365313)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 55741182
          :relative 1.2221924701244788
        )
        :calibrates (3418743 3264907)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 60453643
          :relative 1.275144595382325
        )
        :calibrates (3209040 3207603)
      ))
    :"jpamb.cases.Simple.divideByZero:()I" ((analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 70722952
          :relative 1.3104293075062656
        )
        :calibrates (3463931 3456945)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 55676705
          :relative 1.2143681692314865
        )
        :calibrates (3482303 3314980)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 56632731
          :relative 1.2194181414490335
        )
        :calibrates (3585970 3248099)
      ))
    :"jpamb.cases.Simple.divideZeroByZero:(II)I" ((analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 69000549
          :relative 1.3026704237163516
        )
        :calibrates (3400692 3473349)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 55799188
          :relative 1.209497718351715
        )
        :calibrates (3593475 3295588)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 56879535
          :relative 1.2447435102506132
        )
        :calibrates (3296052 3178989)
      ))
    :"jpamb.cases.Simple.doNothing:()V" ((analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 68967329
          :relative 1.3111304718467525
        )
        :calibrates (3297340 3440845)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 56063886
          :relative 1.2179242725424737
        )
        :calibrates (3568335 3220401)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 56692699
          :relative 1.2422715473799455
        )
        :calibrates (3289125 3201486)
      ))
    :"jpamb.cases.Simple.earlyReturn:()I" ((analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 68684024
          :relative 1.3102215956946541
        )
        :calibrates (3360120 3364444)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 54517237
          :relative 1.2275853774355179
        )
        :calibrates (3282090 3174132)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 56396522
          :relative 1.2341943902266508
        )
        :calibrates (3308252 3269658)
      ))
    :"jpamb.cases.Simple.justAdd:(II)I" ((analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 72221203
          :relative 1.3287310588565684
        )
        :calibrates (3365005 3410843)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 55170783
          :relative 1.2208181719094076
        )
        :calibrates (3384327 3251896)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 56498691
          :relative 1.2387004389983316
        )
        :calibrates (3301900 3219907)
      ))
    :"jpamb.cases.Simple.justMulitply:(II)I" ((analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 69392588
          :relative 1.3127473025971375
        )
        :calibrates (3326409 3428131)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 53760382
          :relative 1.2107773911621702
        )
        :calibrates (3379938 3237882)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 69420833
          :relative 1.3310381803267026
        )
        :calibrates (3272419 3206188)
      ))
    :"jpamb.cases.Simple.justReturn:()I" ((analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 66937675
          :relative 1.2916619150537976
        )
        :calibrates (3422923 3416803)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 54254966
          :relative 1.2232237907602266
        )
        :calibrates (3253354 3236661)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 68672229
          :relative 1.319786863749885
        )
        :calibrates (3285520 3291426)
      ))
    :"jpamb.cases.Simple.justReturnNothing:()V" ((analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 69640351
          :relative 1.3147604761928595
        )
        :calibrates (3346458 3400849)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 55668152
          :relative 1.224843003075533
        )
        :calibrates (3456154 3178126)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" not-found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 56057562
          :relative 1.2333770213102722
        )
        :calibrates (3368342 3182350)
      ))
    :"jpamb.cases.Simple.multiError:(Z)I" ((analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 56371303
          :relative 1.2193005947881295
        )
        :calibrates (3413925 3390438)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 56172382
          :relative 1.2385148967876645
        )
        :calibrates (3298938 3187973)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 69555109
          :relative 1.333322393258619
        )
        :calibrates (3255200 3201887)
      ))
    :"jpamb.cases.Strings.sayHello:(Ljava/lang/String;)V" ((analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 68614093
          :relative 1.3116285261041063
        )
        :calibrates (3414421 3281569)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 54593972
          :relative 1.2320945456999806
        )
        :calibrates (3239559 3158970)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 56300827
          :relative 1.2432422197934028
        )
        :calibrates (3266929 3164427)
      ))
    :"jpamb.cases.Tricky.collatz:(I)V" ((analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 56723080
          :relative 1.223641143748619
        )
        :calibrates (3502532 3276203)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 55203212
          :relative 1.2221957292538417
        )
        :calibrates (3387138 3231957)
      ) (analysis-result
        :response (response
          :predictions (
            :"assertion error" found
            :* skip
            :"divide by zero" skip
            :"null pointer" skip
            :ok skip
            :"out of bounds" skip
          )
        )
        :duration (duration
          :absolute 55777459
          :relative 1.2280074339744693
        )
        :calibrates (3380363 3218685)
      ))
  )
)
