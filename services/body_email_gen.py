def gerar_html_inicio(
    tabelas: list[str],
    total_itens: int,
    total_real_atualizar: int = 0,
    tempo_esperado: str = "Calculando...",
) -> str:
    """Gera o HTML do e-mail de início no formato compatível com o Word/Outlook."""
    tabelas_str = ", ".join(tabelas) if tabelas else "Nenhuma"
    return f"""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
        <html xmlns="http://www.w3.org/1999/xhtml">
        <head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
        <title>Automação Iniciada</title>
        </head>
        <body style="margin: 0; padding: 0; background-color: #f4f5f7; font-family: Arial, Helvetica, sans-serif;">
        <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #f4f5f7; width: 100%;">
            <tr>
            <td align="center" style="padding: 20px 10px;">
                <!--[if (gte mso 9)|(IE)]>
                <table role="presentation" width="600" align="center" border="0" cellspacing="0" cellpadding="0"><tr><td>
                <![endif]-->
                <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" style="max-width: 600px; width: 100%; background-color: #ffffff; border: 1px solid #e1e4e8; border-collapse: collapse;">
                <tr>
                    <td style="background-color: #0052cc; padding: 20px; text-align: center;">
                    <h2 style="color: #ffffff; margin: 0; font-family: Arial, Helvetica, sans-serif; font-size: 20px;">Automação SAP B1: Iniciada</h2>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 25px 20px; font-family: Arial, Helvetica, sans-serif;">
                    <p style="color: #333333; font-size: 15px; margin: 0 0 12px 0;">Olá, equipe,</p>
                    <p style="color: #555555; font-size: 14px; line-height: 20px; margin: 0 0 20px 0;">
                        O script de carga de preços realizou o login no Service Layer com sucesso e iniciou o processamento.
                    </p>
                    <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="10" style="border-collapse: collapse; margin-bottom: 25px;">
                        <tr>
                        <td width="55%" style="border-bottom: 1px solid #eeeeee; color: #555555; font-size: 13px;"><strong>Tabelas na Fila:</strong></td>
                        <td width="45%" style="border-bottom: 1px solid #eeeeee; color: #333333; font-size: 13px;">{len(tabelas)} ({tabelas_str})</td>
                        </tr>
                        <tr>
                        <td style="border-bottom: 1px solid #eeeeee; color: #555555; font-size: 13px;"><strong>Total de Itens nos Arquivos:</strong></td>
                        <td style="border-bottom: 1px solid #eeeeee; color: #333333; font-size: 13px;">{total_itens}</td>
                        </tr>
                        <tr>
                        <td style="border-bottom: 1px solid #eeeeee; color: #555555; font-size: 13px;"><strong>Itens a Atualizar (Delta Real):</strong></td>
                        <td style="border-bottom: 1px solid #eeeeee; color: #0052cc; font-size: 13px;"><strong>{total_real_atualizar}</strong></td>
                        </tr>
                        <tr>
                        <td style="border-bottom: 1px solid #eeeeee; color: #555555; font-size: 13px;"><strong>Tempo Esperado de Execução:</strong></td>
                        <td style="border-bottom: 1px solid #eeeeee; color: #333333; font-size: 13px;">{tempo_esperado}</td>
                        </tr>
                        <tr>
                        <td style="border-bottom: 1px solid #eeeeee; color: #555555; font-size: 13px;"><strong>Janela Limite:</strong></td>
                        <td style="border-bottom: 1px solid #eeeeee; color: #555555; font-size: 13px;">Até 08:00 (Início do expediente)</td>
                        </tr>
                    </table>
                    <p style="color: #888888; font-size: 12px; margin: 0; text-align: center; border-top: 1px solid #f0f0f0; padding-top: 15px;">
                        Gerado automaticamente via Python • Inconel Inox IT
                    </p>
                    </td>
                </tr>
                </table>
                <!--[if (gte mso 9)|(IE)]>
                </td></tr></table>
                <![endif]-->
            </td>
            </tr>
        </table>
        </body>
        </html>"""


def gerar_html_interrupcao(
    tabelas_afetadas: list[str],
    total_atualizados: int,
    motivo: str,
    listas_completas: list[str] | None = None,
    tempo_esperado_restante: str = "Não calculado",
) -> str:
    """Gera o HTML do e-mail de interrupção/erro no formato compatível com o Word/Outlook."""
    tabelas_str = ", ".join(tabelas_afetadas) if tabelas_afetadas else "Nenhuma"
    listas_completas_str = (
        f"{len(listas_completas)} ({', '.join(listas_completas)})"
        if listas_completas
        else "0 (Nenhuma)"
    )
    return f"""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
        <html xmlns="http://www.w3.org/1999/xhtml">
        <head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
        <title>Automação Interrompida</title>
        </head>
        <body style="margin: 0; padding: 0; background-color: #f4f5f7; font-family: Arial, Helvetica, sans-serif;">
        <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #f4f5f7; width: 100%;">
            <tr>
            <td align="center" style="padding: 20px 10px;">
                <!--[if (gte mso 9)|(IE)]>
                <table role="presentation" width="600" align="center" border="0" cellspacing="0" cellpadding="0"><tr><td>
                <![endif]-->
                <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" style="max-width: 600px; width: 100%; background-color: #ffffff; border: 1px solid #dddddd; border-collapse: collapse;">
                <tr>
                    <td style="background-color: #d32f2f; padding: 20px; text-align: center;">
                    <h2 style="color: #ffffff; margin: 0; font-family: Arial, Helvetica, sans-serif; font-size: 20px;">⚠️ Atenção: Automação Interrompida</h2>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 25px 20px; font-family: Arial, Helvetica, sans-serif;">
                    <p style="color: #333333; font-size: 15px; margin: 0 0 10px 0;">Olá, equipe,</p>
                    <p style="color: #555555; font-size: 14px; line-height: 20px; margin: 0 0 15px 0;">
                        A rotina de atualização da lista de preços foi <strong>interrompida</strong> antes de finalizar todos os registros.
                    </p>
                    
                    <!-- Callout Box seguro para Outlook -->
                    <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #fff3f3; border-left: 4px solid #d32f2f; border-collapse: collapse; margin-bottom: 20px;">
                        <tr>
                        <td style="padding: 15px; font-family: Arial, Helvetica, sans-serif;">
                            <h3 style="margin: 0 0 10px 0; color: #d32f2f; font-size: 15px;">Progresso Salvo até a Interrupção</h3>
                            <p style="margin: 0 0 8px 0; color: #333333; font-size: 13px;">
                            <strong>Códigos Atualizados com Sucesso:</strong> {total_atualizados}
                            </p>
                            <p style="margin: 0 0 8px 0; color: #333333; font-size: 13px;">
                            <strong>Listas Já Completas:</strong> {listas_completas_str}
                            </p>
                            <p style="margin: 0 0 8px 0; color: #333333; font-size: 13px;">
                            <strong>Tabelas com Itens Processados:</strong> {tabelas_str}
                            </p>
                            <p style="margin: 0 0 8px 0; color: #333333; font-size: 13px;">
                            <strong>Tempo Estimado para Finalização da Lista:</strong> {tempo_esperado_restante}
                            </p>
                            <p style="margin: 0; color: #c62828; font-size: 13px;">
                            <strong>Motivo / Status:</strong> {motivo}
                            </p>
                        </td>
                        </tr>
                    </table>

                    <p style="color: #555555; font-size: 13px; line-height: 18px; margin: 0 0 20px 0;">
                        Graças à arquitetura de carga delta, ao reiniciar o script, os itens já atualizados acima serão ignorados automaticamente.
                    </p>
                    <p style="color: #888888; font-size: 12px; margin: 0; text-align: center; border-top: 1px solid #f0f0f0; padding-top: 15px;">
                        Mensagem automática gerada pelo script de integração TI • Inconel Inox
                    </p>
                    </td>
                </tr>
                </table>
                <!--[if (gte mso 9)|(IE)]>
                </td></tr></table>
                <![endif]-->
            </td>
            </tr>
        </table>
        </body>
        </html>"""


def gerar_html_conclusao(
    tabelas_processadas: list[str], total_atualizados: int, tempo_total: str
) -> str:
    """Gera o HTML do e-mail de conclusão no formato compatível com o Word/Outlook."""
    tabelas_str = ", ".join(tabelas_processadas) if tabelas_processadas else "Nenhuma"
    return f"""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
        <html xmlns="http://www.w3.org/1999/xhtml">
        <head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
        <title>Atualização Concluída</title>
        </head>
        <body style="margin: 0; padding: 0; background-color: #f4f5f7; font-family: Arial, Helvetica, sans-serif;">
        <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #f4f5f7; width: 100%;">
            <tr>
            <td align="center" style="padding: 20px 10px;">
                <!--[if (gte mso 9)|(IE)]>
                <table role="presentation" width="600" align="center" border="0" cellspacing="0" cellpadding="0"><tr><td>
                <![endif]-->
                <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" style="max-width: 600px; width: 100%; background-color: #ffffff; border: 1px solid #dddddd; border-collapse: collapse;">
                <tr>
                    <td style="background-color: #2e7d32; padding: 20px; text-align: center;">
                    <h2 style="color: #ffffff; margin: 0; font-family: Arial, Helvetica, sans-serif; font-size: 20px;">✅ Atualização Concluída com Sucesso</h2>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 25px 20px; font-family: Arial, Helvetica, sans-serif;">
                    <p style="color: #333333; font-size: 15px; margin: 0 0 10px 0;">Olá, equipe,</p>
                    <p style="color: #555555; font-size: 14px; line-height: 20px; margin: 0 0 15px 0;">
                        A automação da lista de preços foi finalizada com sucesso no SAP B1.
                    </p>
                    
                    <!-- Callout Box seguro para Outlook -->
                    <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #f1f8e9; border-left: 4px solid #2e7d32; border-collapse: collapse; margin-bottom: 20px;">
                        <tr>
                        <td style="padding: 15px; font-family: Arial, Helvetica, sans-serif;">
                            <h3 style="margin: 0 0 10px 0; color: #2e7d32; font-size: 15px;">Resultados Finais</h3>
                            <p style="margin: 0 0 8px 0; color: #333333; font-size: 13px;">
                            <strong>Tabelas Processadas:</strong> {tabelas_str}
                            </p>
                            <p style="margin: 0 0 8px 0; color: #333333; font-size: 13px;">
                            <strong>Itens Atualizados no Total:</strong> {total_atualizados}
                            </p>
                            <p style="margin: 0; color: #333333; font-size: 13px;">
                            <strong>Tempo Total de Execução:</strong> {tempo_total}
                            </p>
                        </td>
                        </tr>
                    </table>

                    <br>
                    <p style="color: #888888; font-size: 12px; margin: 0; text-align: center; border-top: 1px solid #f0f0f0; padding-top: 15px;">
                        Mensagem automática gerada pelo script de integração TI • Inconel Inox
                    </p>
                    </td>
                </tr>
                </table>
                <!--[if (gte mso 9)|(IE)]>
                </td></tr></table>
                <![endif]-->
            </td>
            </tr>
        </table>
        </body>
        </html>"""
