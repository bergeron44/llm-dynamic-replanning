(define (problem maze-navigation)
    (:domain maze)
    (:objects
      agent - agent
      home - location
      victory - store
    )
    (:init
            (= (total-cost) 0)
    )
    
    
  
    
  
    
  
    
  
    
  
    
  
    
  
      
    
    (blocked loc_1_9)
      
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    
    (blocked loc_1_9)
    (blocked loc_0_8)
          
      
    (at agent loc_1_1)
    (at rami_levy_branch_1 loc_3_3)
    (= (item-price milk rami_levy_branch_1) 2.5)
    (selling rami_levy_branch_1 milk)
  (:goal (and (has agent milk)))
    (:metric minimize (total-cost))
    )