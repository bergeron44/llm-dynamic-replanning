(define (domain supermarket-navigation)
  (:requirements :typing)

  (:types
    location agent store item
  )

  (:constants
    agent - agent
  )

  (:predicates
    (at_agent ?agent - agent ?loc - location)
    (at_store ?store - store ?loc - location)
    (connected ?l1 ?l2 - location)
    (selling ?store - store ?item - item)
    (have ?agent - agent ?item - item)
    (blocked ?loc - location)  ; Wall blocking this location
    (clear ?loc - location)    ; Location is not blocked
  )

  (:action drive
    :parameters (?from ?to - location)
    :precondition (and
      (connected ?from ?to)
      (clear ?to)
    )
    :effect (and
      (not (at_agent agent ?from))
      (at_agent agent ?to)
    )
  )

  (:action buy
    :parameters (?item - item ?store - store ?loc - location)
    :precondition (and
      (at_agent agent ?loc)
      (at_store ?store ?loc)
      (selling ?store ?item)
    )
    :effect (and
      (have agent ?item)
    )
  )
)
