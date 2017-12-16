# server_name_env.rb
Facter.add('server_name_env') do
   setcode 'echo $DOMAINS'
end
