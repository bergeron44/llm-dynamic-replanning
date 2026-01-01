(define (problem simple-test)
  (:domain supermarket-navigation)
  (:objects
    agent - agent
    home victory_loc - location
    victory - store
    milk - item
  )
  (:init
    (at_agent agent home)
    (at_store victory victory_loc)
    (selling victory milk)
    (connected home victory_loc)
    (connected victory_loc home)
    (clear victory_loc)
    
  )
  (:goal (and (have agent milk)))
)
