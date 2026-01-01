(define (problem test)
    (:domain supermarket-navigation)
    (:objects
      agent - agent
      loc_1_1 loc_2_2 - location
      victory - store
      milk - item
    )
    (:init
    (at_agent agent loc_3_3)
    (at_store mega_bulldog_tlv loc_4_4)
    (selling mega_bulldog_tlv milk)  )
    (:goal (and (have agent milk)))
    )