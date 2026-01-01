(define (problem temp)
    (:domain supermarket-navigation)
    (:objects
      agent - agent
      home victory_loc - location
      victory - store
      milk - item
    )
    (:init
            (at_store victory victory_loc)
            (connected home victory_loc)
      (connected victory_loc home)
      (clear victory_loc)
    )
    
    (at_agent agent loc_1_1)
    (blocked loc_5_18)
    (at_store mega_bulldog_tlv loc_3_3)
    (blocked loc_5_1)
    (= (item-price milk mega_bulldog_tlv) 3.5)
    (selling mega_bulldog_tlv milk)
  (:goal (and (have agent milk)))
    )