from app import app, db, Projeto, ProjetoMembro, Perfil, MembroPerfil

with app.app_context():
    # Criar novas tabelas
    db.create_all()
    print("✅ Tabelas criadas/atualizadas com sucesso")
    
    # Migrar projetos existentes
    projetos = Projeto.query.all()
    for projeto in projetos:
        # Verificar se já tem perfis
        if Perfil.query.filter_by(projeto_id=projeto.id).first():
            print(f"⏭️  Projeto '{projeto.nome}' já tem perfis, pulando...")
            continue
        
        print(f"📋 Migrando projeto '{projeto.nome}'...")
        
        # Criar perfis padrão
        perfil_admin = Perfil(
            nome="Administrador",
            projeto_id=projeto.id,
            pode_criar_atividade=True,
            pode_editar_atividade=True,
            pode_excluir_atividade=True,
            pode_concluir_qualquer_atividade=True,
            pode_editar_projeto=True,
            pode_gerenciar_membros=True,
            is_default=True
        )
        perfil_membro = Perfil(
            nome="Membro",
            projeto_id=projeto.id,
            pode_criar_atividade=True,
            pode_editar_atividade=True,
            pode_excluir_atividade=False,
            pode_concluir_qualquer_atividade=False,
            pode_editar_projeto=False,
            pode_gerenciar_membros=False,
            is_default=True
        )
        db.session.add(perfil_admin)
        db.session.add(perfil_membro)
        db.session.flush()
        
        # Atribuir perfis aos membros
        membros = ProjetoMembro.query.filter_by(projeto_id=projeto.id).all()
        primeiro_membro = membros[0] if membros else None
        
        for membro in membros:
            # Primeiro membro é admin, outros são membros
            if membro == primeiro_membro:
                db.session.add(MembroPerfil(projeto_membro_id=membro.id, perfil_id=perfil_admin.id))
                print(f"  👤 {membro.user.username} -> Administrador")
            else:
                db.session.add(MembroPerfil(projeto_membro_id=membro.id, perfil_id=perfil_membro.id))
                print(f"  👤 {membro.user.username} -> Membro")
        
        db.session.commit()
        print(f"✅ Projeto '{projeto.nome}' migrado com sucesso\n")
    
    print("🎉 Migração concluída!")
