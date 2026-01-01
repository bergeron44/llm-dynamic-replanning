(define (problem supermarket-navigation-problem)
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
    (blocked loc_4_1)
  (:goal (and (have agent milk)))
    )