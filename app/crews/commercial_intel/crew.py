from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from app.tools.rag_tool import RAGSearchTool
from app.tools.mcp_tool import MCPWebTool, MCPDriveTool
@CrewBase
class CommercialIntelCrew:
    agents_config='config/agents.yaml'; tasks_config='config/tasks.yaml'
    @agent
    def manager(self)->Agent: return Agent(config=self.agents_config['manager'], allow_delegation=True, verbose=True, max_iter=8)
    @agent
    def document_ingestor(self)->Agent: return Agent(config=self.agents_config['document_ingestor'], tools=[MCPDriveTool()], verbose=True, max_iter=5)
    @agent
    def financial_analyst(self)->Agent: return Agent(config=self.agents_config['financial_analyst'], tools=[RAGSearchTool()], verbose=True, max_iter=5)
    @agent
    def market_researcher(self)->Agent: return Agent(config=self.agents_config['market_researcher'], tools=[MCPWebTool()], verbose=True, max_iter=5)
    @agent
    def report_writer_qa(self)->Agent: return Agent(config=self.agents_config['report_writer_qa'], tools=[RAGSearchTool()], verbose=True, max_iter=5)
    @task
    def ingest_task(self)->Task: return Task(config=self.tasks_config['ingest_task'])
    @task
    def analysis_task(self)->Task: return Task(config=self.tasks_config['analysis_task'])
    @task
    def research_task(self)->Task: return Task(config=self.tasks_config['research_task'])
    @task
    def report_task(self)->Task: return Task(config=self.tasks_config['report_task'])
    @crew
    def crew(self)->Crew: return Crew(agents=self.agents, tasks=self.tasks, process=Process.hierarchical, manager_agent=self.manager(), verbose=True, memory=True)
