ip forward-protocol nd
!
no ip http server
no ip http secure-server
!
logging host 172.16.0.1
!
control-plane
!
line con 0
 logging synchronous
line aux 0
line vty 0 4
 login local
 transport input ssh
!
end
