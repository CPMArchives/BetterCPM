COMMAND:
        XOR A
        LD (TOKINDEX),A
        LD HL,OPERANDS
        LD (OPERPTR),HL
CMDLOOP:
        LD A,(TOKINDEX)
        LD B,A
        LD A,(TOKCOUNT)
        CP B
        JP Z,CMDFINIS
        CALL GETTOKEN
        LD A,(HL)
        CP '/'
        JP NZ,CMDOPER
        CALL OPTION
        RET C
        CP 9
        JR NZ,CMDNOTCH
        LD (CHECK),A
        JP CMDNEXT
CMDNOTCH:
        CP 10
        JR NZ,CMDVALUE
        LD (NARROW),A
        JP CMDNEXT
CMDVALUE:
        LD (VALUEID),A
        CALL DESTINAT
        RET C
        LD A,(VALUEID)
        CP 5
        JR NZ,CMDLOCAL
        LD HL,FS_FCB
        LD DE,MASTER
        LD BC,36
        LDIR
        LD A,(DESTDRIV)
        LD (MASTER+36),A
        LD A,(DESTUSER)
        LD (MASTER+37),A
        LD A,1
        LD (MASTSET),A
        JP CMDNEXT
CMDLOCAL:
        CP 6
        LD DE,LOCAL
        JR Z,CMDVALCO
        LD A,1
        LD (CHECK),A
        LD (REFSET),A
        LD DE,REFNAME
CMDVALCO:
        LD HL,FS_FCB
        LD BC,36
        LDIR
        LD A,(VALUEID)
        CP 6
        JR NZ,CMDNEXT
        LD A,1
        LD (LOCALSET),A
        JR CMDNEXT
CMDOPER:
        CALL ADDOPERA
        RET C
CMDNEXT:
        LD A,(TOKINDEX)
        INC A
        LD (TOKINDEX),A
        JP CMDLOOP
CMDFINIS:
        LD A,(CHECK)
        OR A
        JR Z,CMDDEFAU
        LD A,(MASTSET)
        LD B,A
        LD A,(LOCALSET)
        OR B
        SCF
        RET NZ
CMDDEFAU:
CMDIMPLI:
        LD A,(OPERCOUN)
        OR A
        RET NZ
        LD HL,BC_ALL
        LD B,3
        JP ADDOPERA
OPTIONS:
        DB 6,5,'/FILE='
        DB 7,6,'/LOCAL='
        DB 7,8,'/CHECK='
        DB 6,9,'/CHECK'
        DB 3,10,'/40'
        DB 5,11,'/HELP'
        DB 4,12,'/VER'
        DB 0
