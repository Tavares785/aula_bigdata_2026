-- 1. Lista de Contatos: nome de todos os pacientes e seus respectivos telefones, ordenados alfabeticamente.
SELECT nome_paciente, telefone_paciente
FROM Paciente
ORDER BY nome_paciente ASC;

-- 2. Faturamento Total: valor total arrecadado pela clínica até hoje.
SELECT SUM(valor_consulta) AS faturamento_total
FROM Consulta;

-- 3. Agenda do Dia: nome do paciente, nome do médico e hora da consulta para todos os atendimentos.
SELECT p.nome_paciente, m.nome_medico, c.hora_consulta
FROM Consulta c
JOIN Paciente p ON c.fk_cpf_paciente = p.cpf_paciente
JOIN Medico m ON c.fk_crm_medico = m.crm_medico;

-- 4. Pacientes Ausentes: nome de todos os pacientes cadastrados que ainda não realizaram nenhuma consulta.
SELECT p.nome_paciente
FROM Paciente p
LEFT JOIN Consulta c ON p.cpf_paciente = c.fk_cpf_paciente
WHERE c.id_consulta IS NULL;

-- 5. Especialidades Populares: especialidade médica que mais realizou consultas na clínica.
-- (usa subquery com MAX para trazer todas as especialidades empatadas em 1º lugar)
SELECT especialidade_medico, total_consultas
FROM (
    SELECT m.especialidade_medico, COUNT(*) AS total_consultas
    FROM Consulta c
    JOIN Medico m ON c.fk_crm_medico = m.crm_medico
    GROUP BY m.especialidade_medico
) AS contagem
WHERE total_consultas = (SELECT MAX(total_consultas) FROM (
    SELECT COUNT(*) AS total_consultas
    FROM Consulta c
    JOIN Medico m ON c.fk_crm_medico = m.crm_medico
    GROUP BY m.especialidade_medico
) AS maximos);
