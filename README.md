<img align=right width=250 src="/docs/espy.png">

# ES.py :  optimizer, written as a data miner.  

es.py /əˈspī/ verb LITERARY see something that is hidden, or obscure.
  
Break the data up into regions of 'bad' and 'better'. 'Interesting'
things occur at very different frequencies in 'bad' and 'better'.
Find interesting bits. Combine them. Repeat. Nearly all this
processing takes log linear time.

     :-------:                 explore  = better==bad
     | Ba    | Bad <----.      planning = max(better - bad)
     |    56 |          |      monitor  = max(bad - better)
     :-------:------:   |      tabu     = min(bad + better)
             | B    |   v
             |    5 | Better
             :------:

 -h            show help   
 -egs          run all examples   
 -eg S         run examples matching 'S'  
 -ls           list all examples   
 -k I          k Bayes low frequency control  
 -m I          m Bayes low frequency control  
 -best F       size of best set  
 -size F       min size of breaks  
 -cohen F      var min  
 -dir S        dir to data  
 -data S       data file  
 -seed I       random number seed  
